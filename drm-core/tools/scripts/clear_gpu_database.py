#!/usr/bin/env python3
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Get the project root directory
ROOT_DIR = Path(__file__).parent.parent.parent

# Database setup - use the same test database
DB_PATH = ROOT_DIR / "gpu_tracker.db"  # Changed from gpu_tracker.db
DATABASE_URL = f"sqlite:///{DB_PATH}"


def clear_database():
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear all tables
        session.execute(text("DELETE FROM gpu_allocations"))
        session.execute(text("DELETE FROM gpu_instances"))
        session.commit()
        print("Database cleared successfully!")
    except Exception as e:
        print(f"Error clearing database: {e}")
        session.rollback()
    finally:
        session.close()


if __name__ == "__main__":
    # Ask for confirmation
    confirmation = input(
        "Are you sure you want to clear the database? This cannot be undone! (y/N): "
    )
    if confirmation.lower() == "y":
        clear_database()
    else:
        print("Operation cancelled.")
