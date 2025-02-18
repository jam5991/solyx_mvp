from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from drm_core.models import GPUAllocation


@pytest.fixture
def mock_scheduler():
    """Mock Scheduler"""
    scheduler = AsyncMock()
    scheduler.find_available_gpu.return_value = True
    return scheduler


@pytest.mark.asyncio
async def test_job_submission(drm_core, db_session, sample_gpu):
    """Test job submission workflow"""
    job_spec = {
        "job_id": "test-job-1",
        "gpu_type": "NVIDIA A100",
        "min_memory": 70,
        "max_price": 3.0,
        "workload": {"type": "training"},
    }

    with patch.object(
        drm_core.scheduler, "find_available_gpu", return_value=sample_gpu
    ):
        result = await drm_core.submit_job(job_spec)
        assert result is not None
        assert result["status"] == "submitted"
        assert result["job_id"] == "test-job-1"


@pytest.mark.asyncio
async def test_job_submission_no_gpu(drm_core):
    """Test job submission when no GPU is available"""
    job_spec = {
        "job_id": "test-job-2",
        "gpu_type": "NVIDIA A100",
        "min_memory": 1000,  # Unrealistic requirement
        "max_price": 0.1,  # Too low price
        "workload": {"type": "training"},
    }

    with patch.object(
        drm_core.scheduler, "find_available_gpu", return_value=None
    ):
        result = await drm_core.submit_job(job_spec)
        assert result["status"] == "failed"
        assert "No suitable GPU found" in result["reason"]


def test_job_status(drm_core, db_session, sample_gpu):
    """Test job status retrieval"""
    # Create test allocation
    allocation = GPUAllocation(
        gpu_instance_id=sample_gpu.id,
        job_id="test-job-3",
        allocated_at=datetime.utcnow(),
        price_at_allocation=2.5,
    )
    db_session.add(allocation)
    db_session.commit()

    # Test running job status
    status = drm_core.get_job_status("test-job-3")
    assert status is not None
    assert status["status"] == "running"
    assert status["gpu_type"] == sample_gpu.gpu_type

    # Test completed job status
    allocation.released_at = datetime.utcnow()
    allocation.total_energy_consumed_kwh = 1.5
    allocation.total_energy_cost_usd = 0.45
    db_session.commit()

    status = drm_core.get_job_status("test-job-3")
    assert status["status"] == "completed"
    assert status["energy_consumed"] == 1.5
    assert status["energy_cost"] == 0.45


def test_nonexistent_job_status(drm_core):
    """Test status retrieval for non-existent job"""
    status = drm_core.get_job_status("nonexistent-job")
    assert status is None
