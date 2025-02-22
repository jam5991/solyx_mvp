import asyncio
import logging
from typing import Dict, List, Optional

from .config import DRMConfig
from .database import init_database
from .database.repository import GPURepository
from .models import GPUInstance
from .monitoring import JobTracker, ResourceMonitor
from .providers import LambdaLabsProvider, VastAIProvider
from .services import JobManager, Scheduler

logger = logging.getLogger(__name__)


class DRMCore:
    def __init__(self, config: DRMConfig = None, clear_db: bool = False):
        """Initialize DRM Core

        Args:
            config: Configuration object
            clear_db: If True, clear database on startup
        """
        self.config = config or DRMConfig()

        # Initialize database
        self.engine, self.SessionLocal = init_database(
            self.config.get_db_path()
        )
        session = self.SessionLocal()
        self.repo = GPURepository(session)

        # Clear database if requested
        if clear_db:
            logger.info("Clearing database on startup")
            self.repo.clear_database()

        # Initialize components
        self.scheduler = Scheduler(self.repo)
        self.job_manager = JobManager(self.repo, self.scheduler)
        self.job_tracker = JobTracker(self.repo)
        self.resource_monitor = ResourceMonitor()

        # Don't initialize Ray here
        self.ray_service = None

    async def initialize(self):
        """Initialize DRM Core in the correct sequence"""
        logger.info("Initializing DRM Core...")

        # First initialize scheduler providers
        await self.scheduler.initialize_providers(self.config)

        # Then sync with GPU providers asynchronously
        logger.info("Fetching available GPUs from providers...")
        await self.sync_gpu_database()

        # Start monitoring
        await self.resource_monitor.start_monitoring()
        logger.info("DRM Core initialization complete")

    async def initialize_providers(self):
        """Initialize GPU providers and fetch GPUs asynchronously"""
        try:
            logger.info("Setting up providers...")
            providers = {
                "vast": VastAIProvider(self.config.vast_api_key),
                "lambda": LambdaLabsProvider(self.config.lambda_api_key),
            }

            # Create tasks for each provider
            tasks = []
            for name, provider in providers.items():
                logger.info(f"Creating fetch task for {name}...")
                tasks.append(self._fetch_provider_gpus(name, provider))

            # Wait for all provider responses concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_gpus = []
            # Process results without database operations
            for name, result in zip(providers.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"Error fetching from {name}: {result}")
                else:
                    logger.info(f"Found {len(result)} GPUs from {name}")
                    all_gpus.extend(result)

            # Show found GPUs
            logger.info("\n=== Found GPUs ===")
            for gpu in all_gpus:
                logger.info(
                    f"  - {gpu.provider}: {gpu.gpu_type} ({gpu.memory_gb}GB) "
                    f"@ ${gpu.price_per_hour}/hr in {gpu.region}"
                )

            return all_gpus

        except Exception as e:
            logger.error(f"Error initializing providers: {e}")
            return []

    async def _fetch_provider_gpus(
        self, name: str, provider
    ) -> List[GPUInstance]:
        """Fetch GPUs from a single provider"""
        try:
            logger.info(f"Fetching GPUs from {name} provider...")
            gpus = await provider.list_available_gpus()
            logger.info(f"Provider {name} returned {len(gpus)} GPUs:")
            for gpu in gpus:
                logger.info(
                    f"  - {gpu.gpu_type}: {gpu.memory_gb}GB @ ${gpu.price_per_hour}/hr "
                    f"in {gpu.region}"
                )
            return gpus
        except Exception as e:
            logger.error(
                f"Error fetching GPUs from {name}: {str(e)}", exc_info=True
            )
            raise

    async def initialize_ray(self):
        """Initialize Ray only when needed"""
        try:
            if self.ray_service is None:
                logger.info("\n=== Initializing Ray ===")
                from .services.ray_service import (
                    RayService,  # Import here to avoid circular imports
                )

                self.ray_service = RayService()
                await self.ray_service.initialize()
                # Update job manager with ray service
                self.job_manager.ray_service = self.ray_service
                logger.info("Ray initialization complete")
        except Exception as e:
            logger.error(f"Error initializing Ray: {e}")
            raise

    async def submit_job(self, job_spec: Dict) -> Dict:
        """Submit a job for execution"""
        # Initialize Ray only when submitting jobs
        await self.initialize_ray()
        return await self.job_manager.submit_job(job_spec)

    async def sync_gpu_database(self) -> bool:
        """Sync available GPUs to database"""
        gpus = await self.initialize_providers()
        session = self.SessionLocal()
        try:
            # Log current state
            old_count = session.query(GPUInstance).count()
            logger.info(f"\n=== Database Sync ===")
            logger.info(f"Current GPU count in database: {old_count}")

            # Only update if we have new GPUs and the count changed
            if gpus and len(gpus) != old_count:
                logger.info(f"Updating database with {len(gpus)} new GPUs")
                session.query(GPUInstance).delete()
                # Add new GPUs
                for gpu in gpus:
                    session.add(gpu)
                session.commit()

                new_count = session.query(GPUInstance).count()
                logger.info(f"Updated database with {new_count} GPUs")
            else:
                logger.info(f"Keeping existing {old_count} GPUs in database")

            logger.info(f"Database location: {self.config.get_db_path()}")
            return True
        except Exception as e:
            logger.error(f"Error syncing database: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get status of a specific job"""
        try:
            allocation = self.repo.get_allocation_by_job_id(job_id)
            if not allocation:
                return None

            return {
                "job_id": job_id,
                "status": "completed" if allocation.released_at else "running",
                "gpu_type": allocation.gpu_instance.gpu_type,
                "allocated_at": allocation.allocated_at,
                "released_at": allocation.released_at,
                "energy_consumed": allocation.total_energy_consumed_kwh,
                "energy_cost": allocation.total_energy_cost_usd,
            }
        except Exception as e:
            logger.error(f"Error getting job status: {e}")
            return None

    async def shutdown(self):
        """Shutdown the service"""
        await self.job_manager.shutdown()


async def main():
    """Main entry point for the DRM Core service"""
    try:
        # 1. Configuration and API Keys
        logger.info("\n=== Loading Configuration ===")
        config = DRMConfig()

        logger.info("\n=== API Keys Status ===")
        if config.vast_api_key:
            truncated_vast = (
                f"{config.vast_api_key[:8]}...{config.vast_api_key[-8:]}"
            )
            logger.info(f"✓ VAST API Key loaded: {truncated_vast}")
        else:
            logger.error("✗ VAST API Key missing")

        if config.lambda_api_key:
            truncated_lambda = (
                f"{config.lambda_api_key[:8]}...{config.lambda_api_key[-8:]}"
            )
            logger.info(f"✓ Lambda API Key loaded: {truncated_lambda}")
        else:
            logger.error("✗ Lambda API Key missing")

        if not (config.vast_api_key or config.lambda_api_key):
            logger.error(
                "\nNo provider API keys found. Please set VAST_API_KEY and/or LAMBDA_API_KEY in config.env"
            )
            return

        # 2. Initialize Core and Query GPUs
        logger.info("\n=== Initializing DRM Core ===")
        drm = DRMCore(config, clear_db=True)

        logger.info("\n=== Querying GPU Providers ===")
        gpus = await drm.initialize_providers()  # This will print GPU details

        if not gpus:
            logger.error("No GPUs found from any provider!")
            return

        # 3. Initialize Ray (only after we confirm GPUs exist)
        await drm.initialize_ray()

        # 4. Start monitoring and keep running
        await drm.resource_monitor.start_monitoring()
        logger.info("\n=== DRM Core Ready ===")
        logger.info(
            "Service initialized successfully and ready for job submissions"
        )

        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Shutting down DRM Core...")
    except Exception as e:
        logger.error(f"Error running DRM Core: {e}")
        raise
