#!/usr/bin/env python3
import logging
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from drm_core.models import Base, GPUInstance, GPUAllocation

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_schema():
    """Show the database schema and table contents"""
    # Setup database connection
    db_path = Path(__file__).parent.parent.parent / "test_gpu_tracker.db"
    logger.info(f"Database location: {db_path}")

    if not db_path.exists():
        logger.error("Database file not found!")
        return

    engine = create_engine(f"sqlite:///{db_path}")
    inspector = inspect(engine)

    # Get list of all tables
    tables = inspector.get_table_names()
    logger.info(f"Found tables: {tables}")

    # Show all tables
    print("\n📚 Database Tables:")
    for table_name in tables:
        print(f"\n🔹 Table: {table_name}")
        # Get columns for each table
        columns = inspector.get_columns(table_name)
        for column in columns:
            print(f"  - {column['name']}: {column['type']}")
        
        # Get foreign keys for this table
        foreign_keys = inspector.get_foreign_keys(table_name)
        if foreign_keys:
            print("  Foreign Keys:")
            for fk in foreign_keys:
                print(f"    - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
    
    # Show row counts
    print("\n📊 Table Row Counts:")
    with engine.connect() as conn:
        for table in tables:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"- {table}: {count} rows")

    # Show relationships
    print("\n🔗 Relationships:")
    print("- GPUAllocation.gpu_instance_id -> GPUInstance.id (Foreign Key)")
    
    # Show row counts using text()
    with engine.connect() as conn:
        gpu_count = conn.execute(text("SELECT COUNT(*) FROM gpu_instances")).scalar()
        job_count = conn.execute(text("SELECT COUNT(*) FROM gpu_allocations")).scalar()
        
    print(f"\n📊 Current Data:")
    print(f"- GPU Instances: {gpu_count}")
    print(f"- Job Allocations: {job_count}")

    # Show some statistics if there's data
    if gpu_count > 0:
        with engine.connect() as conn:
            # Get GPU providers and counts
            gpu_stats = conn.execute(text("""
                SELECT provider, COUNT(*) as count
                FROM gpu_instances 
                GROUP BY provider
            """)).fetchall()
            
            print("\n🔍 GPU Details by Provider:")
            for provider, count in gpu_stats:
                # Get unique GPU types for this provider
                gpu_types = conn.execute(text("""
                    SELECT DISTINCT gpu_type 
                    FROM gpu_instances 
                    WHERE provider = :provider
                """), {"provider": provider}).fetchall()
                
                types_list = ", ".join(row[0] for row in gpu_types)
                print(f"- {provider}: {count} GPUs")
                print(f"  Types: {types_list}")

if __name__ == "__main__":
    show_schema() 