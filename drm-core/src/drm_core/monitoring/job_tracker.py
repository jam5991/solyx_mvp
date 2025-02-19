import logging
from datetime import datetime
from typing import Dict, Optional

from ..database.repository import GPURepository
from ..models.job import JobStatus

logger = logging.getLogger(__name__)


class JobTracker:
    """Tracks job statuses and resource usage"""

    def __init__(self, repo: GPURepository):
        self.repo = repo
        self.active_jobs: Dict[str, Dict] = {}

    def track_job(
        self, job_id: str, initial_status: JobStatus = JobStatus.PENDING
    ):
        """Start tracking a new job"""
        self.active_jobs[job_id] = {
            "status": initial_status,
            "start_time": datetime.utcnow(),
            "last_updated": datetime.utcnow(),
        }
        logger.info(
            f"Started tracking job {job_id} with status {initial_status}"
        )

    def update_job_status(self, job_id: str, status: JobStatus):
        """Update status of a tracked job"""
        if job_id in self.active_jobs:
            self.active_jobs[job_id].update(
                {"status": status, "last_updated": datetime.utcnow()}
            )
            logger.info(f"Updated job {job_id} status to {status}")

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current status of a job"""
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]

        # Check repository for completed jobs
        allocation = self.repo.get_allocation_by_job_id(job_id)
        if allocation:
            return {
                "status": JobStatus.COMPLETED
                if allocation.released_at
                else JobStatus.RUNNING,
                "start_time": allocation.allocated_at,
                "last_updated": allocation.released_at or datetime.utcnow(),
            }
        return None
