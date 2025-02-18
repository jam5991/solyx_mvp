#!/usr/bin/env python3
import logging
from pathlib import Path

from drm_core.models import Base
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cleanup_database():
    """Remove unused tables and update schema"""
    # Setup database connection
    db_path = Path(__file__).parent.parent.parent / "test_gpu_tracker.db"
    logger.info(f"Database location: {db_path}")

    if not db_path.exists():
        logger.error("Database file not found!")
        return

    engine = create_engine(f"sqlite:///{db_path}")

    try:
        # Drop the gpu_energy_usage table if it exists
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                DROP TABLE IF EXISTS gpu_energy_usage
            """
                )
            )
            conn.commit()
            logger.info("Removed gpu_energy_usage table if it existed")

        # Recreate tables based on current models
        Base.metadata.create_all(engine)
        logger.info("Updated database schema")

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


if __name__ == "__main__":
    cleanup_database()
