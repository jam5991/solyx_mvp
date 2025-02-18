import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict

import ray
from drm_core.models import GPUAllocation, GPUInstance
from drm_core.repository import GPURepository
from drm_core.tracker import EnergyTracker

# Configure root logger only once
logger = logging.getLogger(__name__)


@ray.remote
class RayJobExecutor:
    """Ray actor that executes the actual AI workload"""

    def __init__(self, gpu_config: Dict[str, Any]):
        self.gpu_config = gpu_config
        logging.getLogger("ray").setLevel(logging.ERROR)

        # Ensure required packages are installed
        try:
            pass
        except ImportError:
            logger.warning("PyTorch not found, attempting to install...")
            import subprocess

            subprocess.check_call(["pip", "install", "torch", "torchvision"])

            logger.info("PyTorch installed successfully")

    def execute(self, job_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the AI workload"""
        try:
            import importlib

            module = importlib.import_module(job_spec["workload"]["script"])
            train_fn = getattr(module, job_spec["workload"]["function"])

            # Configure logging to capture training output
            training_logger = logging.getLogger(job_spec["workload"]["script"])
            training_logger.setLevel(logging.INFO)

            # Remove any existing handlers
            training_logger.handlers = []

            # Create a string buffer handler to capture logs
            from io import StringIO

            log_buffer = StringIO()
            buffer_handler = logging.StreamHandler(log_buffer)
            buffer_handler.setFormatter(
                logging.Formatter("%(asctime)s - %(message)s")
            )
            training_logger.addHandler(buffer_handler)

            # Execute training
            result = train_fn(
                data_dir=Path(job_spec["workload"]["data_dir"]),
                epochs=job_spec["workload"]["epochs"],
                batch_size=job_spec["workload"]["batch_size"],
            )

            # Get captured logs
            training_logs = log_buffer.getvalue()

            # Clean up handlers
            training_logger.removeHandler(buffer_handler)
            log_buffer.close()

            return {
                "status": "completed",
                "results": result,
                "logs": training_logs,
            }
        except Exception as e:
            logger.error(
                f"Training failed with error: {str(e)}", exc_info=True
            )
            return {
                "status": "failed",
                "error": str(e),
                "logs": log_buffer.getvalue()
                if "log_buffer" in locals()
                else "",
            }


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
        # If Ray is already initialized properly, don't reinitialize
        if ray.is_initialized():
            logger.info("Ray already initialized, skipping initialization")
            return True

        try:
            logger.info(f"Ray version: {ray.__version__}")
            logger.info("Starting Ray initialization...")

            # Force shutdown any existing Ray instance that might be in a bad state
            ray.shutdown()

            logger.info("Waiting for clean shutdown...")
            time.sleep(1)

            logger.info("Initializing Ray with minimal configuration...")
            ray.init(
                address=None,  # This forces Ray to start a new cluster
                include_dashboard=False,
                ignore_reinit_error=True,
                logging_level=logging.ERROR,
                _system_config={"object_timeout_milliseconds": 200},
            )
            logger.info("Ray initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Ray initialization failed with error: {str(e)}")
            logger.error("Ray initialization stack trace:", exc_info=True)
            raise RuntimeError(f"Failed to initialize Ray: {str(e)}")

    async def submit_job(
        self, job_spec: Dict[str, Any], gpu_instance: GPUInstance
    ) -> Dict[str, Any]:
        """Submit a job for execution"""
        try:
            print("DEBUG: submit_job - Creating actor config")
            gpu_config = {
                "gpu_type": gpu_instance.gpu_type,
                "memory_gb": gpu_instance.memory_gb,
                "instance_id": gpu_instance.instance_id,
            }

            print("DEBUG: submit_job - Creating executor actor")
            executor = RayJobExecutor.remote(gpu_config)

            print("DEBUG: submit_job - Submitting job to executor")
            job_id = job_spec["job_id"]
            future = executor.execute.remote(job_spec)
            self.active_jobs[job_id] = (executor, future)

            # Convert Ray's ObjectRef to a Python awaitable
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: ray.get(future)
            )

            if "logs" in result:
                print(result["logs"], end="")

            # Mark the job as completed in the database
            if result["status"] == "completed":
                self.gpu_repo.release_gpu(job_id)
                del self.active_jobs[job_id]

                # Return completed status instead of submitted
                return {
                    "status": "completed",  # Changed from 'submitted' to 'completed'
                    "job_id": job_id,
                    "gpu_id": gpu_instance.instance_id,
                }

            print("DEBUG: submit_job - Job completed successfully")
            return {
                "status": "failed",  # If we get here, something went wrong
                "job_id": job_id,
                "gpu_id": gpu_instance.instance_id,
            }

        except Exception as e:
            logger.error(f"Error submitting job: {e}")
            # Make sure to release GPU on failure
            self.gpu_repo.release_gpu(job_id)
            return {"status": "failed", "reason": str(e)}

    async def check_job_health(self):
        """Periodic health check for running jobs"""
        now = datetime.now()
        if now - self.last_recovery_check < self.recovery_interval:
            return

        self.last_recovery_check = now

        for job_id, job_info in list(self.active_jobs.items()):
            try:
                # Check if Ray actor is alive
                ray.get(job_info[1].ping.remote(), timeout=5)
            except Exception as e:
                logger.error(f"Job {job_id} appears to have failed: {e}")
                await self.handle_job_failure(job_id, str(e))

    async def handle_job_failure(self, job_id: str, error: str):
        """Handle failed jobs"""
        if job_id not in self.active_jobs:
            return

        # Release GPU
        self.gpu_repo.release_gpu(job_id)

        # Update job status
        self.active_jobs[job_id] = None

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the status of a running job"""
        return {
            "status": "running",  # Simulated status for local development
            "job_id": job_id,
        }

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        return True  # Simulated cancellation for local development

    async def clear_all_jobs(self):
        """Clear all active jobs and their allocations"""
        try:
            logger.info("Clearing all active jobs...")

            # Clear Ray's active jobs
            for job_id, (executor, future) in list(self.active_jobs.items()):
                try:
                    if future:
                        ray.cancel(future, force=True)
                    logger.info(f"Cancelled Ray task for job {job_id}")
                except Exception as e:
                    logger.error(
                        f"Error cancelling Ray task for job {job_id}: {e}"
                    )

            self.active_jobs.clear()

            # Clean up database allocations
            session = self.gpu_repo.session
            try:
                # Get total count of records
                allocation_count = session.query(GPUAllocation).count()

                logger.info(f"Current allocation count: {allocation_count}")

                if allocation_count > 5:
                    # Get IDs of all records except the last 5
                    allocation_to_delete = (
                        session.query(GPUAllocation.id)
                        .order_by(GPUAllocation.allocated_at.desc())
                        .offset(5)
                        .all()
                    )

                    # Delete older records
                    if allocation_to_delete:
                        session.query(GPUAllocation).filter(
                            GPUAllocation.id.in_(
                                [id[0] for id in allocation_to_delete]
                            )
                        ).delete(synchronize_session=False)
                        logger.info(
                            f"Deleted {len(allocation_to_delete)} old allocation records"
                        )

                # Mark remaining GPUs as available
                session.query(GPUInstance).update({"available": True})

                # Mark remaining allocations as released if they're not already
                from datetime import datetime

                session.query(GPUAllocation).filter(
                    GPUAllocation.released_at.is_(None)
                ).update({"released_at": datetime.utcnow()})

                session.commit()

                # Verify the final count
                final_count = session.query(GPUAllocation).count()
                logger.info(f"Final allocation count: {final_count}")

            except Exception as e:
                logger.error(f"Error cleaning database: {e}")
                session.rollback()

            # Only reinitialize Ray if it's in a bad state
            if not ray.is_initialized():
                self._init_ray()

            logger.info("All jobs cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Error clearing jobs: {e}")
            return False

    logger.info(f"Deleted {len(deleted_jobs)} completed jobs from Ray cluster")
