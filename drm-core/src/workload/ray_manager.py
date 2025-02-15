import ray
from typing import Dict, Any, Optional
from ..database.models import GPUInstance, GPUAllocation
from ..database.repository import GPURepository
from ..energy.tracker import EnergyTracker
from datetime import datetime


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
        if not ray.is_initialized():
            ray.init(address="auto")

    async def submit_job(
        self, job_spec: Dict[str, Any], gpu_instance: GPUInstance
    ) -> Optional[str]:
        """
        Submit a job to Ray for execution on the specified GPU
        Returns the Ray job ID if successful
        """
        try:
            # Allocate the GPU in our database
            allocation = self.gpu_repo.allocate_gpu(
                gpu_instance.instance_id, str(job_spec.get("job_id", "unknown"))
            )
            if not allocation:
                return None

            # Create a Ray actor with the GPU configuration
            gpu_config = {
                "gpu_type": gpu_instance.gpu_type,
                "memory_gb": gpu_instance.memory_gb,
                "provider": gpu_instance.provider,
                "instance_id": gpu_instance.instance_id,
            }

            executor = RayJobExecutor.options(
                num_gpus=1,  # Request 1 GPU for this actor
                resources={
                    f"gpu_{gpu_instance.gpu_type}": 1
                },  # Specific GPU type requirement
            ).remote(gpu_config)

            # Track initial energy state
            start_time = datetime.utcnow()

            # Submit the job for execution
            result = await executor.execute.remote(job_spec)

            # Calculate energy usage
            end_time = datetime.utcnow()
            duration_hours = (end_time - start_time).total_seconds() / 3600

            energy_data = self.energy_tracker.calculate_energy_cost(
                gpu_instance, duration_hours
            )

            # Update allocation with energy usage
            self.gpu_repo.update_allocation_energy(
                allocation.id,
                energy_data["energy_consumed_kwh"],
                energy_data["energy_cost_usd"],
                energy_data["power_consumption_watts"],
            )

            # Add detailed energy usage record
            self.gpu_repo.add_energy_usage(gpu_instance.id, allocation.id, energy_data)

            return {"result": ray.get(result), "energy_usage": energy_data}

        except Exception as e:
            # If anything fails, release the GPU
            if allocation:
                self.gpu_repo.release_gpu(gpu_instance.instance_id)
            raise e

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a running Ray job"""
        try:
            result = ray.get(job_id)
            return {"status": "completed", "result": result}
        except ray.exceptions.RayTaskError as e:
            return {"status": "failed", "error": str(e)}
        except Exception as e:
            return {"status": "unknown", "error": str(e)}

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running Ray job"""
        try:
            ray.cancel(job_id)
            return True
        except Exception:
            return False
