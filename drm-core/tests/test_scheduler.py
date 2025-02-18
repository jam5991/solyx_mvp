import pytest
from drm_core.models import GPUAllocation, GPUInstance


@pytest.mark.asyncio
async def test_find_available_gpu(drm_core, db_session, sample_gpu):
    """Test finding available GPU with requirements"""
    requirements = {
        "gpu_type": "NVIDIA A100",
        "min_memory": 70,
        "max_price": 3.0,
    }

    gpu = await drm_core.scheduler.find_available_gpu(**requirements)
    assert gpu is not None
    assert gpu.gpu_type == "NVIDIA A100"
    assert gpu.memory_gb >= requirements["min_memory"]
    assert gpu.price_per_hour <= requirements["max_price"]


@pytest.mark.asyncio
async def test_no_matching_gpu(drm_core, db_session, sample_gpu):
    """Test when no GPU matches requirements"""
    requirements = {
        "gpu_type": "NVIDIA A100",
        "min_memory": 1000,  # Too high memory requirement
        "max_price": 1.0,  # Too low price limit
    }

    gpu = await drm_core.scheduler.find_available_gpu(**requirements)
    assert gpu is None


@pytest.mark.asyncio
async def test_gpu_allocation(drm_core, db_session, sample_gpu):
    """Test GPU allocation process"""
    job_id = "test-allocation-1"

    # Allocate GPU
    allocation = await drm_core.scheduler.allocate_gpu(
        job_id,
        {
            "gpu_type": sample_gpu.gpu_type,
            "min_memory": sample_gpu.memory_gb - 10,
            "max_price": sample_gpu.price_per_hour + 1,
        },
    )

    assert allocation is not None
    assert allocation.job_id == job_id
    assert allocation.gpu_instance_id == sample_gpu.id

    # Verify GPU is marked as unavailable
    gpu = db_session.query(GPUInstance).filter_by(id=sample_gpu.id).first()
    assert not gpu.available


@pytest.mark.asyncio
async def test_gpu_release(drm_core, db_session, sample_gpu):
    """Test GPU release process"""
    job_id = "test-release-1"

    # First allocate a GPU
    allocation = await drm_core.scheduler.allocate_gpu(
        job_id, {"gpu_type": sample_gpu.gpu_type}
    )
    assert allocation is not None

    # Then release it
    await drm_core.scheduler.release_gpu(job_id)

    # Verify GPU is available again
    gpu = db_session.query(GPUInstance).filter_by(id=sample_gpu.id).first()
    assert gpu.available

    # Verify allocation is marked as completed
    allocation = (
        db_session.query(GPUAllocation).filter_by(job_id=job_id).first()
    )
    assert allocation.released_at is not None
