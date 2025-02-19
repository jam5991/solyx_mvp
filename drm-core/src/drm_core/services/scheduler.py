import logging
from typing import Dict, Optional

from ..config import DRMConfig
from ..database.repository import GPURepository
from ..models import GPUInstance
from ..providers.lambdalabs import LambdaLabsProvider
from ..providers.vastai import VastAIProvider

logger = logging.getLogger(__name__)


class Scheduler:
    """Manages GPU allocation and scheduling"""

    def __init__(self, repo: GPURepository):
        self.repo = repo
        self.providers = {}  # Will be initialized when needed
        self.logger = logging.getLogger(__name__)

    async def initialize_providers(self, config: DRMConfig):
        """Initialize GPU providers and sync database"""
        if not self.providers:
            self.providers = {
                "vast": VastAIProvider(config.vast_api_key),
                "lambda": LambdaLabsProvider(config.lambda_api_key),
            }
            logger.info("GPU providers initialized in scheduler")

            # Fetch GPUs from providers and store in database
            for name, provider in self.providers.items():
                try:
                    gpus = await provider.list_available_gpus()
                    logger.info(f"Found {len(gpus)} GPUs from {name}")

                    # Store in database
                    for gpu in gpus:
                        self.repo.add_or_update_gpu(gpu)

                    logger.info(
                        f"Synced {len(gpus)} GPUs from {name} to database"
                    )
                except Exception as e:
                    logger.error(f"Error syncing GPUs from {name}: {e}")

    async def update_gpu_prices(self):
        """Update prices for all tracked GPUs"""
        for name, provider in self.providers.items():
            try:
                gpus = await provider.list_available_gpus()
                for gpu in gpus:
                    self.repo.update_gpu_price(
                        gpu.instance_id, gpu.price_per_hour
                    )
                logger.info(f"Updated prices for {len(gpus)} GPUs from {name}")
            except Exception as e:
                logger.error(f"Error updating prices from {name}: {e}")

    async def find_available_gpu(
        self,
        gpu_type: Optional[str] = None,
        min_memory: int = 8,
        max_price: float = 2.0,
    ) -> Optional[GPUInstance]:
        """Find a suitable GPU matching requirements"""
        # For testing/development, create a mock GPU if no providers
        if not self.providers:
            self.logger.info(
                "No providers configured, creating mock GPU for testing"
            )
            mock_gpu = GPUInstance(
                instance_id="mock-gpu-1",
                provider="mock",
                gpu_type="NVIDIA T4",
                memory_gb=16,
                price_per_hour=1.0,
                region="us-east-1",
            )
            return mock_gpu

        # Real GPU search logic here
        for provider_name, provider in self.providers.items():
            try:
                gpus = await provider.list_available_gpus()
                for gpu in gpus:
                    if (
                        (gpu_type is None or gpu.gpu_type == gpu_type)
                        and gpu.memory_gb >= min_memory
                        and gpu.price_per_hour <= max_price
                    ):
                        return gpu
            except Exception as e:
                self.logger.error(
                    f"Error searching GPUs from {provider_name}: {e}"
                )
                continue

        return None

    async def allocate_gpu(
        self, job_id: str, requirements: Dict
    ) -> Optional[GPUInstance]:
        """Allocate a GPU for a job based on requirements"""
        try:
            gpu = await self.find_available_gpu(
                min_memory=requirements.get("min_memory"),
                max_price=requirements.get("max_price"),
                gpu_type=requirements.get("gpu_type"),
            )

            if not gpu:
                logger.warning(f"No suitable GPU found for job {job_id}")
                return None

            # Track allocation in repository
            self.repo.create_allocation(job_id, gpu.instance_id)
            logger.info(f"Allocated GPU {gpu.instance_id} for job {job_id}")

            return gpu

        except Exception as e:
            logger.error(f"Error allocating GPU for job {job_id}: {e}")
            return None

    def release_gpu(self, job_id: str):
        """Release GPU allocation for a job"""
        try:
            self.repo.release_allocation(job_id)
            logger.info(f"Released GPU allocation for job {job_id}")
        except Exception as e:
            logger.error(f"Error releasing GPU for job {job_id}: {e}")
