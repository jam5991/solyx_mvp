import aiohttp
from typing import List
from .base import CloudGPUProvider, GPUInstance


class VastAIProvider(CloudGPUProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://console.vast.ai/api/v0"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def list_available_gpus(self) -> List[GPUInstance]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/instances/", headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return [
                        GPUInstance(
                            provider="vast.ai",
                            instance_id=str(instance["id"]),
                            gpu_type=instance["gpu_name"],
                            memory_gb=instance["gpu_ram"],
                            price_per_hour=instance["price_per_hour"],
                            region=instance["location"],
                            available=instance["status"] == "available",
                        )
                        for instance in data["instances"]
                    ]
                return []

    # Implement other required methods...
