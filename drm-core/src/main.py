import os
from fastapi import FastAPI, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.orm import Session
from .scheduler.basic_scheduler import BasicScheduler, Job
from .providers.vastai import VastAIProvider
from .providers.coreweave import CoreWeaveProvider
from .providers.lambdalabs import LambdaLabsProvider
from .database.connection import get_db
from .database.repository import GPURepository

app = FastAPI(title="Solyx DRM Service")
scheduler = BasicScheduler()


@app.on_event("startup")
async def startup_event():
    # Initialize all providers with API keys from environment variables
    if os.getenv("VAST_API_KEY"):
        scheduler.add_provider(VastAIProvider(api_key=os.getenv("VAST_API_KEY")))

    if os.getenv("COREWEAVE_API_KEY"):
        scheduler.add_provider(
            CoreWeaveProvider(api_key=os.getenv("COREWEAVE_API_KEY"))
        )

    if os.getenv("LAMBDA_API_KEY"):
        scheduler.add_provider(LambdaLabsProvider(api_key=os.getenv("LAMBDA_API_KEY")))


@app.get("/health")
async def health_check():
    """Kubernetes liveness probe endpoint"""
    return {"status": "healthy"}


@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint"""
    # Check if we have at least one provider configured
    if not scheduler.providers:
        raise HTTPException(status_code=503, detail="No GPU providers configured")
    return {"status": "ready"}


@app.get("/api/v1/gpus")
async def list_available_gpus():
    """Endpoint to list all available GPUs across providers"""
    available_gpus = []
    for provider in scheduler.providers:
        provider_gpus = await provider.list_available_gpus()
        available_gpus.extend(provider_gpus)
    return available_gpus


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
    job_spec: Dict[str, Any], required_memory: int, db: Session = Depends(get_db)
):
    """Submit a new job for execution"""
    gpu_repo = GPURepository(db)
    scheduler = BasicScheduler(gpu_repo)

    # Initialize providers
    if os.getenv("VAST_API_KEY"):
        scheduler.add_provider(VastAIProvider(api_key=os.getenv("VAST_API_KEY")))
    # ... add other providers ...

    job = Job(required_memory=required_memory, job_spec=job_spec)
    result = await scheduler.submit_job(job)

    if not result:
        raise HTTPException(status_code=404, detail="No suitable GPU found for job")

    return result


@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get status of a submitted job"""
    gpu_repo = GPURepository(db)
    scheduler = BasicScheduler(gpu_repo)
    return await scheduler.ray_manager.get_job_status(job_id)
