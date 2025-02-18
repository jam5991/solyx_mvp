from ..base import CloudGPUProvider
import aiohttp
import logging
from typing import List
from ..models import GPUInstance

logger = logging.getLogger(__name__)

class VastAIProvider(CloudGPUProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://console.vast.ai/api/v0"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        logger.info("VastAI provider initialized")

    async def list_available_gpus(self) -> List[GPUInstance]:
        try:
            async with aiohttp.ClientSession() as session:
                logger.info(f"Requesting GPUs from Vast.ai: {self.base_url}/instances/")
                async with session.get(
                    f"{self.base_url}/instances/", headers=self.headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Vast.ai response: {data}")
                        instances = []
                        for instance in data.get("instances", []):
                            try:
                                instances.append(
                                    GPUInstance(
                                        provider="vast.ai",
                                        instance_id=str(instance["id"]),
                                        gpu_type=instance["gpu_name"],
                                        memory_gb=instance["gpu_ram"] / 1024,  # Convert to GB
                                        price_per_hour=instance["dph_total"],
                                        region=instance["geolocation"],
                                        available=instance["actual_status"] == "running"
                                    )
                                )
                                logger.info(f"Added instance: {instance['id']} - {instance['gpu_name']}")
                            except Exception as e:
                                logger.error(f"Error processing instance {instance.get('id')}: {e}")
                                continue
                        return instances
                    else:
                        logger.error(f"Vast.ai error: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error querying Vast.ai: {e}")
            return []
