from pathlib import Path
import asyncio
import logging
import sys
import os
from dotenv import load_dotenv
from .models import Base, GPUInstance, GPUAllocation
from .repository import GPURepository
from .providers.vastai import VastAIProvider
from .providers.lambdalabs import LambdaLabsProvider
from .ray_manager import RayJobManager
from .scheduler import Scheduler
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Dict, List, Optional
from .database.init_db import init_database
import ray

# Configure logging once at the root level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()],
    force=True  # Override any existing handlers
)

# Disable Ray's logging
logging.getLogger("ray").setLevel(logging.ERROR)
logging.getLogger("ray").propagate = False

logger = logging.getLogger(__name__)

class DRMCore:
    def __init__(self, db_url: str = None, init_ray: bool = True):
        """Initialize DRM Core"""
        if db_url is None:
            db_path = Path.cwd() / "gpu_tracker.db"
            db_url = f"sqlite:///{db_path}"
        
        self.db_url = db_url
        
        # Use existing database initialization
        self.engine, self.SessionLocal = init_database(Path(db_url.replace("sqlite:///", "")))
        
        # Load environment variables
        load_dotenv(Path(__file__).parent.parent.parent / "config.env")
        self.lambda_key = os.getenv("LAMBDA_API_KEY")
        self.vast_key = os.getenv("VAST_API_KEY")
        
        # Initialize components
        session = self.SessionLocal()
        self.repo = GPURepository(session)
        self.scheduler = Scheduler(self.repo)
        self.ray_manager = None

    async def initialize(self):
        """Async initialization of providers and database"""
        logger.info("Initializing providers and syncing GPU database...")
        await self.sync_gpu_database()
        
        logger.info("Initializing Ray...")
        self.initialize_ray()
        logger.info("DRM Core initialization complete")

    async def initialize_providers(self):
        """Initialize GPU providers"""
        try:
            logger.info("Setting up providers...")
            self.providers = {
                'vast': VastAIProvider(self.vast_key),
                'lambda': LambdaLabsProvider(self.lambda_key)
            }
            
            all_gpus = []
            for name, provider in self.providers.items():
                try:
                    logger.info(f"Fetching GPUs from {name}...")
                    gpus = await provider.list_available_gpus()
                    logger.info(f"Found {len(gpus)} GPUs from {name}")
                    all_gpus.extend(gpus)
                except Exception as e:
                    logger.error(f"Error fetching GPUs from {name}: {e}")
            
            return all_gpus
        except Exception as e:
            logger.error(f"Error initializing providers: {e}")
            return []

    async def sync_gpu_database(self) -> bool:
        """Sync available GPUs to database"""
        gpus = await self.initialize_providers()
        session = self.SessionLocal()
        try:
            # Clear existing entries
            session.query(GPUInstance).delete()
            # Add new GPUs
            for gpu in gpus:
                session.add(gpu)
            session.commit()
            logger.info(f"Successfully synced {len(gpus)} GPUs to database")
            return True
        except Exception as e:
            logger.error(f"Error syncing database: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    async def submit_job(self, job_spec: Dict) -> Dict:
        """Submit a job for execution"""
        try:
            # Find suitable GPU
            gpu = await self.scheduler.find_available_gpu(
                min_memory=job_spec.get('min_memory'),
                max_price=job_spec.get('max_price'),
                gpu_type=job_spec.get('gpu_type')
            )
            if not gpu:
                return {"status": "failed", "reason": "No suitable GPU found"}

            # Create allocation record in database
            allocation = GPUAllocation(
                gpu_instance_id=gpu.id,
                job_id=job_spec['job_id'],
                allocated_at=datetime.utcnow(),
                price_at_allocation=gpu.price_per_hour
            )
            self.repo.session.add(allocation)
            
            # Mark GPU as not available
            gpu.available = False
            
            # Commit changes to database
            self.repo.session.commit()
            
            logger.info(f"Created allocation for job {job_spec['job_id']} on GPU {gpu.gpu_type}")

            # Submit through Ray manager
            result = await self.ray_manager.submit_job(job_spec, gpu)
            
            if result["status"] == "failed":
                # If job submission fails, mark GPU as available again
                gpu.available = True
                allocation.released_at = datetime.utcnow()
                self.repo.session.commit()
                
            return result
            
        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            return {"status": "failed", "reason": str(e)}

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a specific job"""
        try:
            allocation = self.repo.get_allocation_by_job_id(job_id)
            if not allocation:
                return None
            
            return {
                "job_id": job_id,
                "status": "completed" if allocation.released_at else "running",
                "gpu_type": allocation.gpu_instance.gpu_type,
                "allocated_at": allocation.allocated_at,
                "released_at": allocation.released_at,
                "energy_consumed": allocation.total_energy_consumed_kwh,
                "energy_cost": allocation.total_energy_cost_usd
            }
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return None

    def initialize_ray(self):
        """Initialize Ray (synchronous operation)"""
        if not self.ray_manager:
            self.ray_manager = RayJobManager(self.repo)
            logger.info("Ray initialized")

    async def shutdown(self):
        """Shutdown the service"""
        await self.ray_manager.shutdown()

async def main():
    """Main entry point for DRM Core service"""
    logger.info("Loading configuration...")
    load_dotenv(Path(__file__).parent.parent.parent / "config.env")
    vast_key = os.getenv("VAST_API_KEY")
    lambda_key = os.getenv("LAMBDA_API_KEY")
    logger.info(f"VAST API Key present: {bool(vast_key)}")
    logger.info(f"Lambda API Key present: {bool(lambda_key)}")
    
    # Initialize database first
    engine, SessionLocal = init_database()
    
    # Create DRM Core instance
    drm = DRMCore(db_url=f"sqlite:///{Path.cwd() / 'gpu_tracker.db'}")
    
    # First sync GPUs from providers
    logger.info("Syncing GPUs from providers...")
    await drm.sync_gpu_database()
    
    # Verify GPUs were synced
    session = SessionLocal()
    gpu_count = session.query(GPUInstance).count()
    logger.info(f"Found {gpu_count} GPUs in database")
    
    if gpu_count == 0:
        logger.error("No GPUs found after sync! Check provider API keys and connectivity.")
        return
    
    # Initialize Ray before job submission
    logger.info("Initializing Ray...")
    drm.initialize_ray()
    
    # Generate fake dataset for training
    from .data.generate_fake_data import generate_fake_training_data
    data_dir = generate_fake_training_data()
    logger.info(f"Generated fake dataset at: {data_dir}")
    
    # Generate a unique job ID with name and timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    job_id = f"train-cnn_{timestamp}"
    
    # Create a real training job
    training_job = {
        "job_id": job_id,
        "min_memory": 20,
        "max_price": 3.0,
        "workload": {
            "type": "training",
            "model": "simple_cnn",
            "data_dir": str(data_dir),
            "epochs": 5,
            "batch_size": 32,
            "script": "drm_core.workloads.train_classifier",
            "function": "train_model"
        }
    }
    
    logger.info(f"Created job with ID: {job_id}")
    
    # Clear any existing jobs before starting
    logger.info("Clearing any existing jobs...")
    await drm.ray_manager.clear_all_jobs()
    
    # Now proceed with job submission
    logger.info("Submitting new training job...")
    result = await drm.submit_job(training_job)
    logger.info(f"Training job submission result: {result}")
    
    # Shutdown Ray and exit if job is completed
    if result["status"] == "completed":
        if ray.is_initialized():
            ray.shutdown()
        logger.info("Training completed, shutting down...")
        return  # This will allow the program to exit

if __name__ == "__main__":
    asyncio.run(main()) 