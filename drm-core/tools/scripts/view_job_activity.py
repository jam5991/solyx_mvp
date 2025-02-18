#!/usr/bin/env python3
import logging
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from drm_core.models import GPUInstance, GPUAllocation
from tabulate import tabulate
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def view_job_activity():
    """View all job scheduling activity and GPU allocations"""
    # Use the same database as main.py
    db_path = Path.cwd() / "gpu_tracker.db"
    logger.info(f"Connecting to database at: {db_path}")
    
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query allocations with GPU information
        logger.info("Querying job allocations...")
        allocations = session.query(
            GPUAllocation, GPUInstance
        ).join(
            GPUInstance, GPUAllocation.gpu_instance_id == GPUInstance.id
        ).all()

        if not allocations:
            logger.warning("\n⚠️  No job activity found in database!")
            logger.info("Checking GPU instances table...")
            
            # Check if there are any GPUs in the database
            gpus = session.query(GPUInstance).all()
            if not gpus:
                logger.warning("No GPUs found in database!")
            else:
                logger.info(f"Found {len(gpus)} GPUs but no allocations")
                # Create table for GPUs
                headers = ["GPU Type", "Memory (GB)", "Price/Hour", "Region", "Provider", "Available"]
                table_data = [
                    [
                        gpu.gpu_type,
                        gpu.memory_gb,
                        f"${gpu.price_per_hour:.4f}",
                        gpu.region,
                        gpu.provider,
                        "✓" if gpu.available else "✗"
                    ] for gpu in gpus
                ]
                print("\nAvailable GPUs:")
                print(tabulate(table_data, headers=headers, tablefmt="grid"))
            return

        # Create table for allocations
        headers = ["Job ID", "GPU Type", "Memory (GB)", "Status", "Started", "Price/Hour", "Provider"]
        table_data = [
            [
                alloc.job_id,
                gpu.gpu_type,
                gpu.memory_gb,
                "Active" if not alloc.released_at else "Completed",
                alloc.allocated_at.strftime("%Y-%m-%d %H:%M:%S"),
                f"${gpu.price_per_hour:.4f}",
                gpu.provider
            ] for alloc, gpu in allocations
        ]

        print("\nJob Allocations:")
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    finally:
        session.close()

if __name__ == "__main__":
    view_job_activity() 