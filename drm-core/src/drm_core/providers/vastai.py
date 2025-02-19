import logging
from typing import List

from ..models import GPUInstance
from .base_provider import BaseCloudProvider

logger = logging.getLogger(__name__)


class VastAIProvider(BaseCloudProvider):
    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key, base_url="https://console.vast.ai/api/v0"
        )
        logger.info("VastAI provider initialized")

    async def list_available_gpus(self) -> List[GPUInstance]:
        self.logger.info("\n=== Querying VastAI for available GPUs ===")
        data = await self._make_request("instances/")
        if not data:
            return []

        gpus = [
            self._parse_gpu_instance(instance)
            for instance in data.get("instances", [])
        ]
        self.logger.info(f"\n=== Found {len(gpus)} GPUs from VastAI ===")
        for gpu in gpus:
            self._log_gpu_details(gpu)
        return gpus

    def _parse_gpu_instance(self, instance: dict) -> GPUInstance:
        try:
            gpu = GPUInstance(
                provider="vast.ai",
                id=str(instance["id"]),
                instance_id=str(instance["id"]),
                gpu_type=instance["gpu_name"],
                memory_gb=instance["gpu_ram"] / 1024,
                price_per_hour=instance["dph_total"],
                region=instance["geolocation"],
                available=instance["actual_status"] == "running",
                status="available"
                if instance["actual_status"] == "running"
                else "unavailable",
            )
            self.logger.debug(f"Parsed GPU instance: {gpu}")
            return gpu
        except KeyError as e:
            self.logger.error(f"Missing key while parsing GPU instance: {e}")
            self.logger.debug(f"Raw instance data: {instance}")
            raise
