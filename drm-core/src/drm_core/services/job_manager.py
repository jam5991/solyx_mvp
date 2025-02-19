import logging
from datetime import datetime
from typing import Dict

from ..database.repository import GPURepository
from ..models import GPUAllocation, GPUInstance
from .ray_manager import RayJobManager
from .ray_service import RayService
from .scheduler import Scheduler

logger = logging.getLogger(__name__)


class JobManager:
    def __init__(self, repo: GPURepository, scheduler: Scheduler):
        self.repo = repo
        self.scheduler = scheduler
        self.ray_manager = None  # Don't initialize Ray manager here
        self.ray_service = RayService()

    def _ensure_ray_manager(self):
        """Initialize Ray manager only when needed"""
        if self.ray_manager is None:
            self.ray_manager = RayJobManager(self.repo)

    async def submit_job(self, job_spec: Dict) -> Dict:
        try:
            gpu = await self.scheduler.find_available_gpu(
                min_memory=job_spec.get("min_memory"),
                max_price=job_spec.get("max_price"),
                gpu_type=job_spec.get("gpu_type"),
            )

            if not gpu:
                return {"status": "failed", "reason": "No suitable GPU found"}

            # Initialize Ray only when submitting a job
            self._ensure_ray_manager()

            # Record activity to prevent timeout
            if self.ray_service:
                self.ray_service.record_activity()

            allocation = self._create_allocation(job_spec["job_id"], gpu)
            result = await self.ray_manager.submit_job(job_spec, gpu)

            if result["status"] != "completed":
                await self._handle_failed_submission(allocation)

            return result

        except Exception as e:
            logger.error(f"Job submission failed: {e}")
            return {"status": "failed", "reason": str(e)}

    def _create_allocation(
        self, job_id: str, gpu: GPUInstance
    ) -> GPUAllocation:
        allocation = GPUAllocation(
            gpu_instance_id=gpu.id,
            job_id=job_id,
            allocated_at=datetime.utcnow(),
            price_at_allocation=gpu.price_per_hour,
        )
        self.repo.add_gpu_allocation(allocation)
        return allocation
