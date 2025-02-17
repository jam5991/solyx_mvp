import os
from dotenv import load_dotenv
import logging
from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from drm_core import (
    Scheduler,
    GPURepository,
    VastAIProvider,
    LambdaLabsProvider,
    CoreWeaveProvider
)
from .routes import jobs, gpus
from .database import get_db, engine
from .database.models import Base
from .models.job import JobRequirements, JobStatus

# Load environment variables
load_dotenv("config.env")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Solyx DRM Service")

# Move scheduler initialization into a dependency
def get_scheduler(db: Session = Depends(get_db)) -> Scheduler:
    gpu_repo = GPURepository(db)
    scheduler = Scheduler(gpu_repo)
    
    # Initialize providers with consistent names
    if os.getenv("VAST_API_KEY"):
        scheduler.add_provider(VastAIProvider(api_key=os.getenv("VAST_API_KEY")), "vastai")
    
    if os.getenv("LAMBDA_API_KEY"):
        scheduler.add_provider(LambdaLabsProvider(api_key=os.getenv("LAMBDA_API_KEY")), "lambda")
    
    logger.info(f"Initialized providers: {list(scheduler.providers.keys())}")
    return scheduler

@app.on_event("startup")
async def startup_event():
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

@app.get("/health")
async def health_check(scheduler: Scheduler = Depends(get_scheduler)):
    """Health check endpoint"""
    provider_status = {}
    for name, provider in scheduler.providers.items():
        try:
            # Quick check if provider is responsive
            await provider.list_available_gpus()
            provider_status[name] = "healthy"
        except Exception as e:
            provider_status[name] = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy",
        "providers": provider_status
    }

@app.get("/providers")
async def list_providers(scheduler: Scheduler = Depends(get_scheduler)):
    """List all configured providers and their status"""
    providers = {}
    for name, provider in scheduler.providers.items():
        try:
            gpus = await provider.list_available_gpus()
            providers[name] = {
                "status": "available",
                "gpu_count": len(gpus),
                "gpu_types": list(set(gpu.gpu_type for gpu in gpus)),
                "price_range": {
                    "min": min(gpu.price_per_hour for gpu in gpus) if gpus else None,
                    "max": max(gpu.price_per_hour for gpu in gpus) if gpus else None
                }
            }
        except Exception as e:
            providers[name] = {
                "status": "error",
                "error": str(e)
            }
    
    return providers

@app.get("/api/v1/gpus/summary")
async def gpu_summary(
    scheduler: Scheduler = Depends(get_scheduler),
    provider: str = None
):
    """Get summary of available GPUs"""
    try:
        if provider:
            if provider not in scheduler.providers:
                raise HTTPException(status_code=404, detail=f"Provider {provider} not found")
            gpus = await scheduler.providers[provider].list_available_gpus()
            
            return {
                "provider": provider,
                "total_gpus": len(gpus),
                "by_type": {
                    gpu_type: len([g for g in gpus if g.gpu_type == gpu_type])
                    for gpu_type in set(g.gpu_type for g in gpus)
                },
                "price_stats": {
                    "min": min(g.price_per_hour for g in gpus) if gpus else None,
                    "max": max(g.price_per_hour for g in gpus) if gpus else None,
                    "avg": sum(g.price_per_hour for g in gpus) / len(gpus) if gpus else None
                }
            }
        else:
            # Show stats grouped by provider
            provider_stats = {}
            total_gpus = 0
            
            for prov_name, provider in scheduler.providers.items():
                gpus = await provider.list_available_gpus()
                total_gpus += len(gpus)
                
                provider_stats[prov_name] = {
                    "gpu_count": len(gpus),
                    "by_type": {
                        gpu_type: len([g for g in gpus if g.gpu_type == gpu_type])
                        for gpu_type in set(g.gpu_type for g in gpus)
                    },
                    "price_stats": {
                        "min": min(g.price_per_hour for g in gpus) if gpus else None,
                        "max": max(g.price_per_hour for g in gpus) if gpus else None,
                        "avg": sum(g.price_per_hour for g in gpus) / len(gpus) if gpus else None
                    }
                }

            return {
                "total_gpus": total_gpus,
                "providers": provider_stats
            }
            
    except Exception as e:
        logger.error(f"Error in gpu_summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ready")
async def readiness_check(scheduler: Scheduler = Depends(get_scheduler)):
    """Kubernetes readiness probe endpoint"""
    if not scheduler.providers:
        raise HTTPException(status_code=503, detail="No GPU providers configured")
    return {"status": "ready"}


@app.get("/api/v1/gpus")
async def list_available_gpus(scheduler: Scheduler = Depends(get_scheduler)):
    """Endpoint to list all available GPUs across providers"""
    try:
        available_gpus = []
        for provider in scheduler.providers:
            logger.info(f"Querying provider: {provider.__class__.__name__}")
            provider_gpus = await provider.list_available_gpus()
            logger.info(f"Found {len(provider_gpus)} GPUs from provider")
            available_gpus.extend(provider_gpus)
        return available_gpus
    except Exception as e:
        logger.error(f"Error listing GPUs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/find-gpu")
async def find_gpu(required_memory: int):
    """Find the best GPU for given requirements"""
    job = Job(required_memory=required_memory)
    gpu = await scheduler.find_best_gpu(job)
    if not gpu:
        raise HTTPException(status_code=404, detail="No suitable GPU found")
    return gpu


@app.post("/api/v1/jobs")
async def submit_job(
    requirements: JobRequirements,
    scheduler: Scheduler = Depends(get_scheduler)
):
    """Submit a new job with MVP requirements"""
    try:
        gpu = await scheduler.select_best_gpu(requirements.dict())
        if not gpu:
            raise HTTPException(
                status_code=404, 
                detail="No GPU found matching requirements"
            )
        
        return {
            "status": "success",
            "gpu": {
                "provider": gpu.provider,
                "instance_id": gpu.instance_id,
                "memory_gb": gpu.memory_gb,
                "price_per_hour": gpu.price_per_hour
            }
        }
    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    scheduler: Scheduler = Depends(get_scheduler)
):
    """Get status of a specific job"""
    try:
        status = await scheduler.get_job_status(job_id)
        if not status:
            raise HTTPException(
                status_code=404,
                detail=f"Job {job_id} not found"
            )
        return status

    except Exception as e:
        logger.error(f"Error getting job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/jobs")
async def list_jobs(
    scheduler: Scheduler = Depends(get_scheduler),
    status: Optional[JobStatus] = None
):
    """List all jobs, optionally filtered by status"""
    try:
        jobs = await scheduler.list_jobs(status)
        return {
            "total": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
