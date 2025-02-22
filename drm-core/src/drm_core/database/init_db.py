import logging
from pathlib import Path
from typing import Tuple, Type

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..models import Base  # Updated import

logger = logging.getLogger(__name__)


def init_database(db_path: Path) -> Tuple[Engine, Type[Session]]:
    """Initialize the database connection and create tables"""
    try:
        # Ensure the parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert Path to string and ensure proper URI format
        db_url = f"sqlite:///{db_path.absolute()}"
        logger.info(f"Initializing database at: {db_url}")

        # Create engine with better SQLite settings
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},  # Allow multi-threading
            echo=False,  # Set to True for SQL debugging
        )

        # Create session factory
        SessionLocal = sessionmaker(
            bind=engine, autocommit=False, autoflush=False
        )

        # Create tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)

        return engine, SessionLocal

    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database(Path.cwd() / "gpu_tracker.db")

from .init_db import init_database

__all__ = ["init_database"]
