from .vastai import VastAIProvider
from .lambdalabs import LambdaLabsProvider
from .coreweave import CoreWeaveProvider
from typing import List, Dict, Any
from abc import ABC, abstractmethod
from ..models import GPUInstance

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
        pass

    @abstractmethod
    async def get_gpu_by_id(self, instance_id: str) -> GPUInstance:
        """Get a specific GPU instance by ID"""
        pass

    @abstractmethod
    async def create_instance(self, gpu_type: str, region: str) -> GPUInstance:
        """Create a new GPU instance"""
        pass

    @abstractmethod
    async def terminate_instance(self, instance_id: str) -> bool:
        """Terminate a GPU instance"""
        pass

__all__ = ['VastAIProvider', 'LambdaLabsProvider', 'CoreWeaveProvider', 'query_lambda_labs', 'query_vast_ai']
