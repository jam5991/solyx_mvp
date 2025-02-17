#!/usr/bin/env python3
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from drm_core.database.models import Base
from drm_core.database.repository import GPURepository
from drm_core.providers.vastai import VastAIProvider
from drm_core.providers.lambdalabs import LambdaLabsProvider
from drm_core.providers.coreweave import CoreWeaveProvider
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def update_gpu_database():
    """Query providers and update GPU database"""
    # Load environment variables from config.env
    config_path = Path(__file__).parent.parent.parent / "config.env"
    if not config_path.exists():
        logger.error(f"Config file not found at: {config_path}")
        return
    
    load_dotenv(dotenv_path=config_path)
    logger.info(f"Loaded config from: {config_path}")
    
    # Setup database
    db_path = Path(__file__).parent.parent.parent / "test_gpu_tracker.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        repo = GPURepository(session)
        providers = {}
        
        # Initialize providers with API keys
        if vast_key := os.getenv("VAST_API_KEY"):
            providers["vast.ai"] = VastAIProvider(vast_key)
            logger.info("Added Vast.ai provider")
        
        if lambda_key := os.getenv("LAMBDA_API_KEY"):
            providers["lambda"] = LambdaLabsProvider(lambda_key)
            logger.info("Added Lambda Labs provider")
            
        if coreweave_key := os.getenv("COREWEAVE_API_KEY"):
            providers["coreweave"] = CoreWeaveProvider(coreweave_key)
            logger.info("Added CoreWeave provider")
        
        if not providers:
            logger.error("No API keys found in config.env! Please check your configuration.")
            return
        
        logger.info(f"Querying providers: {', '.join(providers.keys())}")
        
        # Query each provider and store GPUs
        total_gpus = 0
        for name, provider in providers.items():
            try:
                logger.info(f"\nQuerying {name}...")
                gpus = await provider.list_available_gpus()
                
                if not gpus:
                    logger.warning(f"No GPUs found for {name}")
                    continue
                
                for gpu in gpus:
                    stored_gpu = repo.add_gpu_instance(gpu)
                    logger.info(f"""
Stored GPU from {name}:
- Type: {stored_gpu.gpu_type}
- Memory: {stored_gpu.memory_gb}GB
- Price: ${stored_gpu.price_per_hour}/hour
- Region: {stored_gpu.region}
- ID: {stored_gpu.instance_id}
""")
                total_gpus += len(gpus)
                logger.info(f"✅ Stored {len(gpus)} GPUs from {name}")
                
            except Exception as e:
                logger.error(f"Error querying {name}: {str(e)}")
        
        logger.info(f"\n📊 Summary: Stored {total_gpus} GPUs total")
        
    except Exception as e:
        logger.error(f"Error updating database: {str(e)}")
        raise  # Re-raise for debugging
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(update_gpu_database()) 