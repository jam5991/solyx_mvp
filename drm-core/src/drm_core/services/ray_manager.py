import asyncio
import logging
from typing import Any, Dict

import ray

from ..database.repository import GPURepository
from ..models import GPUInstance

logger = logging.getLogger(__name__)


@ray.remote
class RayJobExecutor:
    def __init__(self, gpu_config: Dict[str, Any]):
        self.gpu_config = gpu_config
        logging.getLogger("ray").setLevel(logging.ERROR)

    async def execute(self, job_spec: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import importlib

            # Import the module and get the function
            module = importlib.import_module(job_spec["workload"]["script"])
            train_fn = getattr(module, job_spec["workload"]["function"])

            # Extract only the function arguments from workload
            workload = job_spec["workload"].copy()
            # Remove the module and function names from args
            workload.pop("script")
            workload.pop("function")

            # Call the function with the remaining arguments
            result = train_fn(**workload)
            return {"status": "completed", "result": result}
        except Exception as e:
            logger.error(f"Job execution failed: {e}")
            return {"status": "failed", "error": str(e)}


class RayJobManager:
    def __init__(self, gpu_repo: GPURepository):
        self.gpu_repo = gpu_repo
        self.active_jobs: Dict[str, tuple] = {}
        self._ray_initialized = False

    def _ensure_ray_initialized(self):
        if not self._ray_initialized and not ray.is_initialized():
            logger.info("Initializing Ray for job execution...")
            ray.init(ignore_reinit_error=True)
            self._ray_initialized = True

    async def submit_job(
        self, job_spec: Dict[str, Any], gpu_instance: GPUInstance
    ) -> Dict[str, Any]:
        self._ensure_ray_initialized()

        try:
            gpu_config = {
                "gpu_type": gpu_instance.gpu_type,
                "memory_gb": gpu_instance.memory_gb,
                "instance_id": gpu_instance.instance_id,
            }

            executor = RayJobExecutor.remote(gpu_config)
            job_id = job_spec["job_id"]
            future = executor.execute.remote(job_spec)
            self.active_jobs[job_id] = (executor, future)

            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ray.get(future)
            )

            if result["status"] == "completed":
                del self.active_jobs[job_id]
                return {
                    "status": "completed",
                    "job_id": job_id,
                    "gpu_id": gpu_instance.instance_id,
                }

            return {
                "status": "failed",
                "job_id": job_id,
                "gpu_id": gpu_instance.instance_id,
                "reason": result.get("error", "Unknown error"),
            }

        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            return {"status": "failed", "reason": str(e)}

    async def clear_all_jobs(self) -> bool:
        try:
            for job_id, (executor, future) in self.active_jobs.items():
                ray.kill(executor)
            self.active_jobs.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing jobs: {e}")
            return False
