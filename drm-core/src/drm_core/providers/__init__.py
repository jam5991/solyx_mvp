from abc import ABC, abstractmethod
from typing import Any, Dict, List

from ..models import GPUInstance
from .base_provider import BaseCloudProvider
from .lambdalabs import LambdaLabsProvider
from .vastai import VastAIProvider


async def query_lambda_labs() -> List[Dict[str, Any]]:
    """Mock function for querying Lambda Labs API"""
    return []


async def query_vast_ai() -> List[Dict[str, Any]]:
    """Mock function for querying Vast.ai API"""
    return []


class CloudGPUProvider(ABC):
    """Base class for cloud GPU providers"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def list_available_gpus(self) -> List[GPUInstance]:
        """List all available GPUs from this provider"""

    @abstractmethod
    async def get_gpu_by_id(self, instance_id: str) -> GPUInstance:
        """Get a specific GPU instance by ID"""

    @abstractmethod
    async def create_instance(self, gpu_type: str, region: str) -> GPUInstance:
        """Create a new GPU instance"""

    @abstractmethod
    async def terminate_instance(self, instance_id: str) -> bool:
        """Terminate a GPU instance"""


__all__ = [
    "BaseCloudProvider",
    "VastAIProvider",
    "LambdaLabsProvider",
    "query_lambda_labs",
    "query_vast_ai",
]
