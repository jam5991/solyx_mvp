from ..base import CloudGPUProvider
import aiohttp
import logging
from typing import List
from ..models import GPUInstance

logger = logging.getLogger(__name__)

class LambdaLabsProvider(CloudGPUProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        logger.info("LambdaLabs provider initialized")

    async def list_available_gpus(self) -> List[GPUInstance]:
        try:
            async with aiohttp.ClientSession() as session:
                logger.info("Requesting instances from Lambda Labs")
                async with session.get(
                    f"{self.base_url}/instances",
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        logger.error(f"Lambda Labs API error: {response.status}")
                        return []
                    
                    data = await response.json()
                    gpus = []
                    
                    for instance in data.get("data", []):
                        try:
                            gpu = GPUInstance(
                                provider="lambda",
                                instance_id=instance.get("id"),
                                gpu_type=instance.get("instance_type", {}).get("name", "Unknown"),
                                memory_gb=instance.get("instance_type", {}).get("specs", {}).get("memory_gib", 0),
                                price_per_hour=instance.get("instance_type", {}).get("price_cents_per_hour", 0) / 100,
                                region=instance.get("region", {}).get("name", "Unknown"),
                                available=instance.get("status") == "active"
                            )
                            gpus.append(gpu)
                        except Exception as e:
                            logger.error(f"Error processing Lambda Labs instance: {e}")
                            continue
                    
                    return gpus
        except Exception as e:
            logger.error(f"Error querying Lambda Labs: {e}")
            return []
