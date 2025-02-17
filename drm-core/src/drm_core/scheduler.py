from typing import Dict, List, Optional
from .models import GPUInstance
from .repository import GPURepository
from .providers import CloudGPUProvider
import logging

logger = logging.getLogger(__name__)

class Scheduler:
    """Manages GPU allocation and scheduling"""
    
    def __init__(self, gpu_repository: GPURepository):
        self.repo = gpu_repository
        self.providers: Dict[str, CloudGPUProvider] = {}
        
    def add_provider(self, provider: CloudGPUProvider, name: str):
        """Add a GPU provider to the scheduler"""
        self.providers[name] = provider
        logger.info(f"Added provider: {name}")
    
    async def update_gpu_prices(self):
        """Update prices for all tracked GPUs"""
        for name, provider in self.providers.items():
            try:
                gpus = await provider.list_available_gpus()
                for gpu in gpus:
                    self.repo.update_gpu_price(gpu.instance_id, gpu.price_per_hour)
                logger.info(f"Updated prices for {len(gpus)} GPUs from {name}")
            except Exception as e:
                logger.error(f"Error updating prices from {name}: {e}")
    
    async def find_available_gpu(self, 
                               min_memory: Optional[int] = None,
                               max_price: Optional[float] = None,
                               gpu_type: Optional[str] = None,
                               provider: Optional[str] = None) -> Optional[GPUInstance]:
        """Find an available GPU matching the requirements"""
        try:
            # Query all providers for current availability
            available_gpus = []
            for name, provider_instance in self.providers.items():
                if provider and name != provider:
                    continue
                    
                try:
                    gpus = await provider_instance.list_available_gpus()
                    available_gpus.extend(gpus)
                except Exception as e:
                    logger.error(f"Error querying provider {name}: {e}")
            
            # Filter GPUs based on requirements
            filtered_gpus = []
            for gpu in available_gpus:
                if min_memory and gpu.memory_gb < min_memory:
                    continue
                if max_price and gpu.price_per_hour > max_price:
                    continue
                if gpu_type and gpu.gpu_type != gpu_type:
                    continue
                filtered_gpus.append(gpu)
            
            # Sort by price and return cheapest
            if filtered_gpus:
                return sorted(filtered_gpus, key=lambda g: g.price_per_hour)[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding available GPU: {e}")
            return None
    
    async def allocate_gpu(self, job_id: str, requirements: Dict) -> Optional[GPUInstance]:
        """Allocate a GPU for a job based on requirements"""
        try:
            gpu = await self.find_available_gpu(
                min_memory=requirements.get('min_memory'),
                max_price=requirements.get('max_price'),
                gpu_type=requirements.get('gpu_type'),
                provider=requirements.get('provider')
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