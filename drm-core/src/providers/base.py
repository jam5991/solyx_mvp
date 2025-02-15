from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime


class GPUInstance:
    def __init__(
        self,
        provider: str,
        instance_id: str,
        gpu_type: str,
        memory_gb: int,
        price_per_hour: float,
        region: str,
        available: bool,
    ):
        self.provider = provider
        self.instance_id = instance_id
        self.gpu_type = gpu_type
        self.memory_gb = memory_gb
        self.price_per_hour = price_per_hour
        self.region = region
        self.available = available
        self.last_updated = datetime.utcnow()


class CloudGPUProvider(ABC):
    """Base class for cloud GPU providers"""

    @abstractmethod
    async def list_available_gpus(self) -> List[GPUInstance]:
        """List all available GPU instances from this provider"""
        pass

    @abstractmethod
    async def get_gpu_price(self, instance_id: str) -> float:
        """Get current price for a specific GPU instance"""
        pass

    @abstractmethod
    async def allocate_gpu(self, instance_id: str) -> bool:
        """Attempt to allocate/reserve a GPU instance"""
        pass

    @abstractmethod
    async def deallocate_gpu(self, instance_id: str) -> bool:
        """Release a GPU instance"""
        pass
