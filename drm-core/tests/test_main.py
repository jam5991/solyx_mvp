import pytest
from unittest.mock import patch, AsyncMock
from drm_core.main import DRMCore
from drm_core.models import GPUInstance, GPUAllocation
from datetime import datetime

@pytest.mark.asyncio
async def test_drm_core_initialization(drm_core):
    """Test DRM Core initialization"""
    assert drm_core.repo is not None
    assert drm_core.scheduler is not None
    assert drm_core.ray_manager is not None

@pytest.mark.asyncio
async def test_sync_gpu_database(drm_core, mock_providers):
    """Test GPU database synchronization"""
    await drm_core.sync_gpu_database()
    
    # Verify that providers were called
    mock_providers['vast'].list_available_gpus.assert_called_once()
    mock_providers['lambda'].list_available_gpus.assert_called_once()

@pytest.mark.asyncio
async def test_submit_and_track_job(drm_core, db_session, sample_gpu):
    """Test end-to-end job submission and tracking"""
    job_spec = {
        "job_id": "test-main-1",
        "gpu_type": "NVIDIA A100",
        "min_memory": 70,
        "max_price": 3.0,
        "workload": {"type": "training"}
    }
    
    # Submit job
    with patch.object(drm_core.scheduler, 'find_available_gpu', return_value=sample_gpu):
        result = await drm_core.submit_job(job_spec)
        assert result["status"] == "submitted"
    
    # Create allocation for tracking
    allocation = GPUAllocation(
        gpu_instance_id=sample_gpu.id,
        job_id="test-main-1",
        allocated_at=datetime.utcnow(),
        price_at_allocation=2.5
    )
    db_session.add(allocation)
    db_session.commit()
    
    # Check job status
    status = drm_core.get_job_status("test-main-1")
    assert status is not None
    assert status["status"] == "running"

@pytest.mark.asyncio
async def test_error_handling(drm_core):
    """Test error handling in main DRM Core functions"""
    # Test with invalid job spec
    result = await drm_core.submit_job({})
    assert result["status"] == "failed"
    
    # Test with non-existent job status
    status = drm_core.get_job_status("nonexistent-job")
    assert status is None

@pytest.mark.asyncio
async def test_shutdown(drm_core, mock_ray):
    """Test DRM Core shutdown"""
    await drm_core.shutdown()
    mock_ray['shutdown'].assert_called_once()

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 