#!/usr/bin/env python3
import argparse
import logging
from pathlib import Path

from drm_core.database.models import (
    Base,
    GPUAllocation,
    GPUEnergyUsage,
    GPUInstance,
)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_job_activity(db_path: Path, clear_all: bool = False):
    """Clear job activity from the database"""
    if not db_path.exists():
        logger.error(f"Database not found at: {db_path}")
        return

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Get current counts
        allocation_count = session.query(GPUAllocation).count()
        gpu_count = session.query(GPUInstance).count()
        energy_count = session.query(GPUEnergyUsage).count()

        logger.info("\n📊 Current Database Status:")
        logger.info(f"- Job Allocations: {allocation_count}")
        logger.info(f"- GPU Instances: {gpu_count}")
        logger.info(f"- Energy Usage Records: {energy_count}")

        if clear_all:
            # Delete all data
            session.query(GPUEnergyUsage).delete()
            session.query(GPUAllocation).delete()
            session.query(GPUInstance).delete()
            logger.info("\n🗑️  Cleared all data from database")
        else:
            # Only clear job activity
            session.query(GPUEnergyUsage).delete()
            session.query(GPUAllocation).delete()
            logger.info("\n🗑️  Cleared job activity (kept GPU instances)")

        session.commit()

        # Verify deletion
        new_allocation_count = session.query(GPUAllocation).count()
        new_gpu_count = session.query(GPUInstance).count()
        new_energy_count = session.query(GPUEnergyUsage).count()

        logger.info("\n✅ New Database Status:")
        logger.info(f"- Job Allocations: {new_allocation_count}")
        logger.info(f"- GPU Instances: {new_gpu_count}")
        logger.info(f"- Energy Usage Records: {new_energy_count}")

    except Exception as e:
        logger.error(f"Error clearing database: {e}")
        session.rollback()
    finally:
        session.close()


def reset_database(db_path: Path):
    """Reset database to initial state"""
    if db_path.exists():
        try:
            engine = create_engine(f"sqlite:///{db_path}")
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            logger.info("✅ Database reset successfully")
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
    else:
        logger.error(f"Database not found at: {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Manage DRM Core job activity"
    )
    parser.add_argument(
        "--action",
        choices=["clear", "clear-all", "reset"],
        required=True,
        help="Action to perform",
    )
    args = parser.parse_args()

    db_path = Path(__file__).parent.parent.parent / "test_gpu_tracker.db"

    if args.action == "clear":
        clear_job_activity(db_path, clear_all=False)
    elif args.action == "clear-all":
        clear_job_activity(db_path, clear_all=True)
    elif args.action == "reset":
        reset_database(db_path)
