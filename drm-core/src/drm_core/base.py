import logging
from typing import List

from models import GPUInstance

logger = logging.getLogger(__name__)


class CloudGPUProvider:
    """Base class for cloud GPU providers"""

    async def list_available_gpus(self) -> List[GPUInstance]:
        raise NotImplementedError

    async def get_gpu_price(self, instance_id: str) -> float:
        raise NotImplementedError
