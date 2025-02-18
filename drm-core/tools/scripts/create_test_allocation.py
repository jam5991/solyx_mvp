#!/usr/bin/env python3
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from drm_core.models import Base, GPUInstance, GPUAllocation
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_allocation():
    """Create a test job allocation for an existing GPU"""
    # Setup database connection
    db_path = Path(__file__).parent.parent.parent / "test_gpu_tracker.db"
    logger.info(f"Using database at: {db_path}")

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get first available GPU
        gpu = session.query(GPUInstance).filter_by(available=True).first()
        
        if not gpu:
            logger.error("No available GPUs found in database!")
            return

        logger.info(f"Found GPU: {gpu.gpu_type} ({gpu.instance_id})")

        # Create a test allocation with all required fields
        allocation = GPUAllocation(
            gpu_instance_id=gpu.id,
            job_id="test-job-1",
            allocated_at=datetime.utcnow(),
            released_at=None,
            price_at_allocation=gpu.price_per_hour,  # Use current GPU price
            total_energy_consumed_kwh=0.0,
            total_energy_cost_usd=0.0,
            average_power_consumption_watts=0.0
        )

        session.add(allocation)
        session.commit()

        logger.info(f"""
Created test allocation:
- Job ID: {allocation.job_id}
- GPU: {gpu.gpu_type}
- GPU Instance ID: {gpu.instance_id}
- Price at allocation: ${allocation.price_at_allocation}/hr
- Allocated at: {allocation.allocated_at}
""")

    except Exception as e:
        logger.error(f"Error creating test allocation: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    create_test_allocation() 