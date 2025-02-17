#!/usr/bin/env python3
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from drm_core.database.models import Base, GPUInstance
from tabulate import tabulate
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database(engine):
    """Initialize database tables if they don't exist"""
    print("Initializing database...")
    Base.metadata.create_all(engine)
    print("Database initialized.")

def view_stored_gpus():
    """View all GPUs stored in the database"""
    # Use the same database path as test_drm_core.py
    db_path = Path(__file__).parent.parent.parent / "test_gpu_tracker.db"
    logger.info(f"Using database at: {db_path.absolute()}")

    if not db_path.exists():
        logger.error(f"Database not found at: {db_path}")
        return

    engine = create_engine(f"sqlite:///{db_path}")
    
    # Initialize database if needed
    init_database(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query all GPU instances
        gpus = session.query(GPUInstance).all()
        
        if not gpus:
            logger.warning("\n⚠️  No GPUs found in database!")
            logger.info("Try running the integration test:")
            logger.info("USE_REAL_PROVIDERS=true python -m pytest tests/test_drm_core.py -v")
            return

        # Prepare data for tabulation
        gpu_data = []
        for gpu in gpus:
            try:
                region = json.loads(gpu.region) if gpu.region.startswith('{') else gpu.region
            except:
                region = gpu.region

            gpu_data.append([
                gpu.instance_id,
                gpu.provider,
                gpu.gpu_type,
                f"{gpu.memory_gb}GB",
                f"${gpu.price_per_hour:.2f}/hr",
                region,
                "✅" if gpu.available else "❌",
                gpu.created_at.strftime("%Y-%m-%d %H:%M:%S")
            ])

        # Print table
        headers = ["Instance ID", "Provider", "GPU Type", "Memory", "Price", "Region", "Available", "Created At"]
        print("\n🖥️  Stored GPU Instances:")
        print(tabulate(gpu_data, headers=headers, tablefmt="pretty"))
        
        # Print summary
        providers = set(gpu.provider for gpu in gpus)
        gpu_types = set(gpu.gpu_type for gpu in gpus)
        available = sum(1 for gpu in gpus if gpu.available)
        
        print("\n📊 Summary:")
        print(f"Total GPUs: {len(gpus)}")
        print(f"Available GPUs: {available}")
        print(f"Providers: {', '.join(providers)}")
        print(f"GPU Types: {', '.join(gpu_types)}")

    except Exception as e:
        logger.error(f"Error viewing GPUs: {e}")
        raise
    finally:
        session.close()

def view_provider_gpus(provider_name: str):
    """View GPUs for a specific provider"""
    # ... setup code ...
    gpus = session.query(GPUInstance).filter(
        GPUInstance.provider == provider_name
    ).all()
    # ... display code ...

if __name__ == "__main__":
    view_stored_gpus() 