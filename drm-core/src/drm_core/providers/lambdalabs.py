import logging
from typing import List

from ..models import GPUInstance
from .base_provider import BaseCloudProvider

logger = logging.getLogger(__name__)


class LambdaLabsProvider(BaseCloudProvider):
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key, base_url="https://cloud.lambdalabs.com/api/v1"
        )
        logger.info("LambdaLabs provider initialized")

    async def list_available_gpus(self) -> List[GPUInstance]:
        """List available GPUs from Lambda Labs"""
        self.logger.info("Fetching available GPUs from Lambda Labs...")
        data = await self._make_request("instances")
        if not data:
            self.logger.warning("No data received from Lambda Labs API")
            return []

        instances = data.get("data", [])
        gpus = []

        for instance in instances:
            try:
                # Extract instance type info
                instance_type = instance.get("instance_type", {})
                region = instance.get("region", {})

                gpu = GPUInstance(
                    provider="lambda",
                    id=instance["id"],
                    instance_id=instance["id"],  # Use same ID for both fields
                    gpu_type=instance_type.get("name", "unknown"),
                    memory_gb=float(
                        instance_type.get("description", "0 GB")
                        .split("(")[1]
                        .split("GB")[0]
                        .strip()
                    ),
                    price_per_hour=instance_type.get("price_cents_per_hour", 0)
                    / 100.0,  # Convert cents to dollars
                    region=region.get("description", "unknown"),
                    available=instance.get("status") == "active",
                    status="available"
                    if instance.get("status") == "active"
                    else "unavailable",
                )
                gpus.append(gpu)
                self.logger.debug(f"Parsed Lambda Labs GPU instance: {gpu}")
            except Exception as e:
                self.logger.error(
                    f"Error parsing instance {instance.get('id')}: {e}"
                )
                continue

        self.logger.info(f"Found {len(gpus)} GPUs from Lambda Labs")
        for gpu in gpus:
            self._log_gpu_details(gpu)
        return gpus

    def _parse_gpu_instance(self, instance: dict) -> GPUInstance:
        try:
            gpu = GPUInstance(
                provider="lambda",
                instance_id=instance["id"],
                gpu_type=instance["instance_type"],
                memory_gb=instance["specs"]["memory_gib"],
                price_per_hour=instance["price_per_hour"],
                region=instance["region"],
                available=instance["status"] == "available",
            )
            self.logger.debug(f"Parsed Lambda Labs GPU instance: {gpu}")
            return gpu
        except KeyError as e:
            self.logger.error(
                f"Missing key while parsing Lambda Labs GPU instance: {e}"
            )
            self.logger.debug(f"Raw instance data: {instance}")
            raise
