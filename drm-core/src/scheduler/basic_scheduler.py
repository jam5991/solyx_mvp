from typing import List, Optional, Dict, Any
from ..providers.base import GPUInstance
from ..database.repository import GPURepository
from ..workload.ray_manager import RayJobManager


class Job:
    def __init__(self, required_memory: int, job_spec: Dict[str, Any]):
        self.required_memory = required_memory
        self.job_spec = job_spec


class BasicScheduler:
    def __init__(self, gpu_repo: GPURepository):
        self.providers = []
        self.gpu_repo = gpu_repo
        self.ray_manager = RayJobManager(gpu_repo)

    def add_provider(self, provider):
        self.providers.append(provider)

    async def submit_job(self, job: Job) -> Optional[Dict[str, Any]]:
        """
        Find suitable GPU and submit job for execution
        Returns job submission details if successful
        """
        # Find best GPU for the job
        gpu = await self.find_best_gpu(job)
        if not gpu:
            return None

        # Submit job to Ray for execution
        try:
            result = await self.ray_manager.submit_job(job.job_spec, gpu)
            return {
                "job_id": job.job_spec.get("job_id"),
                "gpu": gpu,
                "status": "submitted",
                "ray_result": result,
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def find_best_gpu(self, job: Job) -> Optional[GPUInstance]:
        """
        Simple scheduling algorithm that finds the cheapest suitable GPU
        that meets the job's requirements
        """
        available_gpus = []
        for provider in self.providers:
            provider_gpus = await provider.list_available_gpus()
            available_gpus.extend(provider_gpus)

        # Filter GPUs that meet minimum requirements
        suitable_gpus = [
            gpu
            for gpu in available_gpus
            if gpu.memory_gb >= job.required_memory and gpu.available
        ]

        if not suitable_gpus:
            return None

        # Find cheapest option
        return min(suitable_gpus, key=lambda g: g.price_per_hour)
