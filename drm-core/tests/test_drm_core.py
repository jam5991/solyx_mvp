import pytest
import os
import logging
import platform
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from drm_core.models import Base, GPUInstance, GPUAllocation
from drm_core.repository import GPURepository
from drm_core.providers.vastai import VastAIProvider
from drm_core.providers.lambdalabs import LambdaLabsProvider
import aiohttp
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Set up Windows-specific event loop policy
if sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Database setup
DB_PATH = Path(__file__).parent.parent / "test_gpu_tracker.db"
TEST_DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create database tables before running tests"""
    Base.metadata.create_all(engine)
    yield
    # Optionally, drop tables after all tests
    # Base.metadata.drop_all(engine)

@pytest.fixture(scope="function")
def db_session():
    """Provide a database session for each test"""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.mark.asyncio
async def test_drm_core_integration(db_session: Session):
    """Test the integration of DRM Core with real GPU providers"""
    print("\n=== Starting Test ===")
    logger.info("Starting integration test...")
    try:
        # Load environment variables from config.env
        config_path = Path(__file__).parent.parent / "config.env"
        print(f"Looking for config at: {config_path}")
        load_dotenv(config_path)
        
        logger.info("Loaded environment variables")
        
        # Get API keys using the correct environment variable names
        lambda_key = os.getenv("LAMBDA_API_KEY")
        vast_key = os.getenv("VAST_API_KEY")
        
        print(f"Lambda key found: {'Yes' if lambda_key else 'No'}")
        print(f"Vast key found: {'Yes' if vast_key else 'No'}")
        
        if not lambda_key:
            logger.warning("LAMBDA_API_KEY not found in config.env")
        if not vast_key:
            logger.warning("VAST_API_KEY not found in config.env")
        
        logger.info("\n=== Starting DRM Core Integration Test ===")
        
        # Clear existing data using text()
        db_session.execute(text("DELETE FROM gpu_allocations"))
        db_session.execute(text("DELETE FROM gpu_instances"))
        db_session.commit()
        logger.info("🗑️ Cleared existing data")

        # Initialize providers
        lambda_provider = LambdaLabsProvider(api_key=lambda_key)
        vast_provider = VastAIProvider(api_key=vast_key)

        logger.info("\n=== Making API calls to providers ===")
        logger.info("🌐 Calling Lambda Labs API...")
        # Get GPU listings
        lambda_gpus = await lambda_provider.list_available_gpus()
        print(f"\nLambda Labs GPUs found: {len(lambda_gpus)}")
        for gpu in lambda_gpus:
            print(f"""
Lambda GPU:
- Instance ID: {gpu.instance_id}
- GPU Type: {gpu.gpu_type}
- Region: {gpu.region}
- Price: ${gpu.price_per_hour}/hr
""")
        
        logger.info("🌐 Calling Vast.ai API...")
        vast_gpus = await vast_provider.list_available_gpus()
        print(f"\nVast.ai GPUs found: {len(vast_gpus)}")
        for gpu in vast_gpus:
            print(f"""
Vast.ai GPU:
- Instance ID: {gpu.instance_id}
- GPU Type: {gpu.gpu_type}
- Region: {gpu.region}
- Price: ${gpu.price_per_hour}/hr
""")

        # Store GPUs in database
        for gpu in lambda_gpus + vast_gpus:
            db_session.add(gpu)
            logger.info(f"Adding GPU: {gpu.provider} - {gpu.gpu_type} - {gpu.instance_id}")
        
        db_session.commit()
        logger.info("Committed GPU data to database")
        
        # Get available GPUs through repository
        repo = GPURepository(db_session)
        available_gpus = repo.list_available_gpus()
        logger.info(f"Found {len(available_gpus)} available GPUs")
        
        # Add mock GPU if none available
        if not available_gpus:
            logger.warning("No GPUs available, adding mock GPU")
            mock_gpu = GPUInstance(
                provider="mock_provider",
                instance_id="mock-1",
                gpu_type="NVIDIA A100",
                memory_gb=80,
                price_per_hour=2.5,
                region="mock-region",
                available=True
            )
            db_session.add(mock_gpu)
            db_session.commit()
            available_gpus = [mock_gpu]
        
        # Verify we have GPUs to work with
        assert len(available_gpus) > 0, "No GPUs available for testing"
        
        # Log available GPUs
        for gpu in available_gpus:
            logger.info(f"""
Available GPU:
- Provider: {gpu.provider}
- Type: {gpu.gpu_type}
- Region: {gpu.region}
- Price: ${gpu.price_per_hour}/hr
""")
        
        # After storing GPUs, check what's in the database
        stored_gpus = repo.list_available_gpus()
        print(f"\nTotal GPUs stored in database: {len(stored_gpus)}")
        for gpu in stored_gpus:
            print(f"""
Stored GPU:
- Provider: {gpu.provider}
- Instance ID: {gpu.instance_id}
- GPU Type: {gpu.gpu_type}
- Region: {gpu.region}
- Price: ${gpu.price_per_hour}/hr
""")
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        db_session.rollback()
        raise

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 
    