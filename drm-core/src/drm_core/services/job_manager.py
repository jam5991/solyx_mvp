import logging
from typing import Dict

from ..database.repository import GPURepository
from ..models import GPUAllocation, GPUInstance
from .ray_manager import RayJobManager
from .scheduler import Scheduler

logger = logging.getLogger(__name__)


class JobManager:
    def __init__(self, repo: GPURepository, scheduler: Scheduler):
        self.repo = repo
        self.scheduler = scheduler
        self.ray_manager = None
        self.logger = logging.getLogger(__name__)

    def _ensure_ray_manager(self):
        """Initialize Ray manager only when needed"""
        if self.ray_manager is None:
            self.ray_manager = RayJobManager(self.repo)

    async def _handle_failed_submission(self, allocation: GPUAllocation):
        """Handle cleanup when job submission fails"""
        if allocation:
            logger.info(
                f"Cleaning up failed job allocation: {allocation.job_id}"
            )
            self.repo.release_gpu(allocation.job_id)

    def _create_allocation(
        self, job_id: str, gpu: GPUInstance
    ) -> GPUAllocation:
        """Create a new GPU allocation for a job"""
        return self.repo.allocate_gpu(gpu.instance_id, job_id)

    async def submit_job(self, job_spec: Dict) -> Dict:
        """Submit a job for execution"""
        try:
            # Ensure Ray manager is initialized
            self._ensure_ray_manager()

            # Allocate GPU
            gpu = await self.scheduler.find_available_gpu(
                job_spec.get("gpu_type"),
                job_spec.get("min_memory", 8),
                job_spec.get("max_price", 2.0),
            )

            if not gpu:
                return {"status": "failed", "reason": "No suitable GPU found"}

            # Submit job through Ray manager
            result = await self.ray_manager.submit_job(job_spec, gpu)

            if result["status"] == "completed":
                self.logger.info(
                    f"Job {job_spec['job_id']} completed successfully"
                )
                return {
                    "status": "completed",
                    "job_id": job_spec["job_id"],
                    "gpu_id": gpu.instance_id,
                    "result": result.get("result", {}),
                }
            else:
                self.logger.error(
                    f"Job {job_spec['job_id']} failed: {result.get('reason')}"
                )
                return {
                    "status": "failed",
                    "job_id": job_spec["job_id"],
                    "reason": result.get("reason", "Unknown error"),
                }

        except Exception as e:
            self.logger.error(f"Job submission failed: {e}")
            return {"status": "failed", "reason": str(e)}
