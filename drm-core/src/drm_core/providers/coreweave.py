from ..base import CloudGPUProvider
import aiohttp
import logging
from typing import List
from ..models import GPUInstance

logger = logging.getLogger(__name__)

class CoreWeaveProvider(CloudGPUProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.coreweave.com/v2"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def list_available_gpus(self) -> List[GPUInstance]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/compute/available", headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        GPUInstance(
                            provider="coreweave",
                            instance_id=instance["id"],
                            gpu_type=instance["gpu"]["model"],
                            memory_gb=instance["gpu"]["memory"],
                            price_per_hour=instance["pricing"]["hourly"],
                            region=instance["region"],
                            available=True,
                        )
                        for instance in data["instances"]
                    ]
                return []

    async def get_gpu_price(self, instance_id: str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/compute/instances/{instance_id}/price",
                headers=self.headers,
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return float(data["hourly_rate"])
                return 0.0
