import ray
import logging
from typing import Dict, Any, Optional
from ..database.models import GPUInstance, GPUAllocation
from ..database.repository import GPURepository
from ..energy.tracker import EnergyTracker
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@ray.remote
class RayJobExecutor:
    """Ray actor that executes the actual AI workload"""

    def __init__(self, gpu_config: Dict[str, Any]):
        self.gpu_config = gpu_config

    async def execute(self, job_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the AI workload with the given specifications
        Returns job results or error information
        """
        try:
            # Here you would implement the actual AI workload execution
            # This is a placeholder that would be replaced with real ML/AI code
            return {
                "status": "completed",
                "results": f"Job executed on {self.gpu_config['gpu_type']}",
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}


class RayJobManager:
    def __init__(self, gpu_repo: GPURepository):
        self.gpu_repo = gpu_repo
        self.energy_tracker = EnergyTracker()
        self.active_jobs = {}
        self.recovery_interval = timedelta(minutes=5)
        self.last_recovery_check = datetime.now()
        
        # Initialize Ray
        self._init_ray()

    def _init_ray(self):
        """Initialize Ray with proper error handling"""
        try:
            if not ray.is_initialized():
                ray.init(local_mode=True)
                logger.info("Ray initialized in local mode")
        except Exception as e:
            logger.error(f"Ray initialization failed: {e}")
            raise RuntimeError("Failed to initialize Ray")

    async def submit_job(
        self, 
        job_spec: Dict[str, Any], 
        gpu_instance: GPUInstance
    ) -> Optional[Dict[str, Any]]:
        """Submit a job with failure recovery"""
        allocation = None
        try:
            # Check energy costs and potentially delay job
            region = gpu_instance.region
            current_cost = await self.energy_tracker.get_current_cost(region)
            
            if current_cost > job_spec.get("max_energy_cost", float("inf")):
                optimal_time = await self.energy_tracker.find_optimal_execution_window(
                    region=region,
                    duration_hours=job_spec.get("estimated_duration", 1)
                )
                if optimal_time > datetime.now():
                    return {
                        "status": "delayed",
                        "scheduled_start": optimal_time,
                        "reason": "high_energy_cost"
                    }

            # Allocate GPU
            allocation = self.gpu_repo.allocate_gpu(
                gpu_instance.instance_id,
                str(job_spec.get("job_id", "unknown"))
            )
            if not allocation:
                return None

            # Create Ray actor
            executor = RayJobExecutor.remote(gpu_instance.to_dict())
            
            # Track job
            self.active_jobs[job_spec["job_id"]] = {
                "executor": executor,
                "gpu_instance": gpu_instance,
                "start_time": datetime.now(),
                "last_heartbeat": datetime.now(),
                "status": "running"
            }

            # Submit job
            future = executor.execute.remote(job_spec)
            
            return {
                "status": "submitted",
                "job_id": job_spec["job_id"],
                "gpu": gpu_instance.to_dict(),
                "ray_future": future
            }

        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            if allocation:
                self.gpu_repo.release_gpu(gpu_instance.instance_id)
            if job_spec.get("job_id") in self.active_jobs:
                del self.active_jobs[job_spec["job_id"]]
            return None

    async def check_job_health(self):
        """Periodic health check for running jobs"""
        now = datetime.now()
        if now - self.last_recovery_check < self.recovery_interval:
            return

        self.last_recovery_check = now
        
        for job_id, job_info in list(self.active_jobs.items()):
            try:
                # Check if Ray actor is alive
                ray.get(job_info["executor"].ping.remote(), timeout=5)
                job_info["last_heartbeat"] = now
            except Exception as e:
                logger.error(f"Job {job_id} appears to have failed: {e}")
                await self.handle_job_failure(job_id, str(e))

    async def handle_job_failure(self, job_id: str, error: str):
        """Handle failed jobs"""
        if job_id not in self.active_jobs:
            return

        job_info = self.active_jobs[job_id]
        gpu_instance = job_info["gpu_instance"]

        # Release GPU
        self.gpu_repo.release_gpu(gpu_instance.instance_id)
        
        # Update job status
        job_info["status"] = "failed"
        job_info["error"] = error
        job_info["end_time"] = datetime.now()

        # Cleanup
        try:
            ray.kill(job_info["executor"])
        except:
            pass

        # Remove from active jobs
        del self.active_jobs[job_id]

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a running job"""
        return {
            "status": "running",  # Simulated status for local development
            "job_id": job_id
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        return True  # Simulated cancellation for local development
