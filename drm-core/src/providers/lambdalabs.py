import aiohttp
from typing import List
from .base import CloudGPUProvider, GPUInstance


class LambdaLabsProvider(CloudGPUProvider):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://cloud.lambdalabs.com/api/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    async def list_available_gpus(self) -> List[GPUInstance]:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/instance-types", headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    instances = []
                    for instance_type in data["data"]:
                        if instance_type[
                            "available_regions"
                        ]:  # Only include if available somewhere
                            for region in instance_type["available_regions"]:
                                instances.append(
                                    GPUInstance(
                                        provider="lambda_labs",
                                        instance_id=f"{instance_type['name']}-{region}",
                                        gpu_type=instance_type["gpu_name"],
                                        memory_gb=instance_type["gpu_memory_gb"],
                                        price_per_hour=float(
                                            instance_type["price_per_hour"]
                                        ),
                                        region=region,
                                        available=True,
                                    )
                                )
                    return instances
                return []

    async def get_gpu_price(self, instance_id: str) -> float:
        # Lambda Labs prices are fixed per instance type
        instance_type, region = instance_id.rsplit("-", 1)
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/instance-types", headers=self.headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    for instance in data["data"]:
                        if instance["name"] == instance_type:
                            return float(instance["price_per_hour"])
                return 0.0

    async def allocate_gpu(self, instance_id: str) -> bool:
        instance_type, region = instance_id.rsplit("-", 1)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/instance-operations/launch",
                headers=self.headers,
                json={
                    "instance_type_name": instance_type,
                    "region_name": region,
                    "quantity": 1,
                },
            ) as response:
                return response.status == 200

    async def deallocate_gpu(self, instance_id: str) -> bool:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/instance-operations/terminate",
                headers=self.headers,
                json={"instance_ids": [instance_id]},
            ) as response:
                return response.status == 200
