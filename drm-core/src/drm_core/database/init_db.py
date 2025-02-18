import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import (  # Explicitly import all models
    Base,
    GPUAllocation,
    GPUInstance,
)

logger = logging.getLogger(__name__)


def init_database(db_path: Path = None):
    """Initialize the database and create all tables"""
    if db_path is None:
        db_path = Path.cwd() / "gpu_tracker.db"

    logger.info(f"Initializing database at: {db_path}")

    # Create database URL
    db_url = f"sqlite:///{db_path}"

    # Create engine
    engine = create_engine(db_url)

    # Create all tables
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(engine)
        logger.info("Created tables:")
        for table in Base.metadata.tables:
            logger.info(f"- {table}")
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise

    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    logger.info("Database initialization complete")
    return engine, SessionLocal


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database()
