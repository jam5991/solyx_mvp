import logging
from typing import List

import aiohttp
from base import CloudGPUProvider
from models import GPUInstance

logger = logging.getLogger(__name__)


class LambdaLabsProvider(CloudGPUProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.logger = logging.getLogger(__name__)
        logger.info("LambdaLabs provider initialized")

    async def list_available_gpus(self) -> List[GPUInstance]:
        """List available GPUs from Lambda Labs"""
        try:
            self.logger.info("Requesting instances from Lambda Labs")
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(
                    f"{self.base_url}/instances"
                ) as response:
                    data = await response.json()
                    self.logger.info(f"Lambda Labs response: {data}")

                    instances = []
                    for instance in data.get("data", []):
                        try:
                            gpu = GPUInstance(
                                provider="lambda",
                                instance_id=instance["id"],
                                gpu_type=instance["instance_type"][
                                    "gpu_description"
                                ],
                                memory_gb=instance["instance_type"]["specs"][
                                    "memory_gib"
                                ],
                                price_per_hour=instance["instance_type"][
                                    "price_cents_per_hour"
                                ]
                                / 100,
                                region=instance["region"]["name"],
                                available=True,
                            )
                            instances.append(gpu)
                            self.logger.info(
                                f"Added instance: {gpu.instance_id} - {gpu.gpu_type}"
                            )
                        except Exception as e:
                            logger.error(
                                f"Error processing Lambda Labs instance: {e}"
                            )
                            continue

                    return instances
        except Exception as e:
            logger.error(f"Error fetching Lambda Labs instances: {e}")
            return []
