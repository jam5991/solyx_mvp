import pytest
from datetime import datetime, timedelta
from drm_core.models import GPUInstance, GPUAllocation
from drm_core.repository import GPURepository

@pytest.fixture
def gpu_repo(db_session):
    """Create a GPU repository instance"""
    return GPURepository(db_session)

def test_add_gpu_instance(gpu_repo, db_session):
    """Test adding a new GPU instance"""
    gpu = GPUInstance(
        provider="test_provider",
        instance_id="test-2",
        gpu_type="NVIDIA A100",
        memory_gb=80,
        price_per_hour=2.5,
        region="test-region",
        available=True
    )
    
    # Add GPU
    added_gpu = gpu_repo.add_gpu_instance(gpu)
    assert added_gpu.id is not None
    assert added_gpu.instance_id == "test-2"
    
    # Verify in database
    stored_gpu = db_session.query(GPUInstance).filter_by(instance_id="test-2").first()
    assert stored_gpu is not None
    assert stored_gpu.gpu_type == "NVIDIA A100"

def test_update_existing_gpu(gpu_repo, db_session, sample_gpu):
    """Test updating an existing GPU instance"""
    # Modify GPU properties
    updated_gpu = GPUInstance(
        provider=sample_gpu.provider,
        instance_id=sample_gpu.instance_id,
        gpu_type=sample_gpu.gpu_type,
        memory_gb=90,  # Changed memory
        price_per_hour=3.0,  # Changed price
        region=sample_gpu.region,
        available=True
    )
    
    # Update GPU
    result = gpu_repo.add_gpu_instance(updated_gpu)
    assert result.memory_gb == 90
    assert result.price_per_hour == 3.0
    
    # Verify in database
    stored_gpu = db_session.query(GPUInstance).filter_by(id=sample_gpu.id).first()
    assert stored_gpu.memory_gb == 90
    assert stored_gpu.price_per_hour == 3.0

def test_get_gpu_by_id(gpu_repo, sample_gpu):
    """Test retrieving GPU by ID"""
    gpu = gpu_repo.get_gpu_by_id(sample_gpu.instance_id)
    assert gpu is not None
    assert gpu.id == sample_gpu.id
    assert gpu.gpu_type == sample_gpu.gpu_type

def test_get_nonexistent_gpu(gpu_repo):
    """Test retrieving non-existent GPU"""
    gpu = gpu_repo.get_gpu_by_id("nonexistent-id")
    assert gpu is None

def test_gpu_allocation(gpu_repo, db_session, sample_gpu):
    """Test GPU allocation creation and retrieval"""
    # Create allocation
    allocation = GPUAllocation(
        gpu_instance_id=sample_gpu.id,
        job_id="test-job-4",
        allocated_at=datetime.utcnow(),
        price_at_allocation=sample_gpu.price_per_hour
    )
    
    added_allocation = gpu_repo.add_gpu_allocation(allocation)
    assert added_allocation.id is not None
    assert added_allocation.job_id == "test-job-4"
    
    # Test retrieval by job ID
    stored_allocation = gpu_repo.get_allocation_by_job_id("test-job-4")
    assert stored_allocation is not None
    assert stored_allocation.gpu_instance_id == sample_gpu.id

def test_get_gpu_allocations(gpu_repo, db_session, sample_gpu):
    """Test retrieving allocation history for a GPU"""
    # Create multiple allocations
    allocations = []
    for i in range(3):
        allocation = GPUAllocation(
            gpu_instance_id=sample_gpu.id,
            job_id=f"test-job-history-{i}",
            allocated_at=datetime.utcnow() - timedelta(hours=i),
            price_at_allocation=sample_gpu.price_per_hour
        )
        db_session.add(allocation)
        allocations.append(allocation)
    db_session.commit()
    
    # Retrieve allocation history
    history = gpu_repo.get_gpu_allocations(sample_gpu.id)
    assert len(history) == 3
    assert all(a.gpu_instance_id == sample_gpu.id for a in history)

def test_allocation_lifecycle(gpu_repo, db_session, sample_gpu):
    """Test complete allocation lifecycle"""
    # Create allocation
    allocation = GPUAllocation(
        gpu_instance_id=sample_gpu.id,
        job_id="test-job-lifecycle",
        allocated_at=datetime.utcnow(),
        price_at_allocation=sample_gpu.price_per_hour
    )
    
    # Add and verify initial state
    added_allocation = gpu_repo.add_gpu_allocation(allocation)
    assert added_allocation.released_at is None
    assert added_allocation.total_energy_consumed_kwh is None
    
    # Update with completion data
    added_allocation.released_at = datetime.utcnow()
    added_allocation.total_energy_consumed_kwh = 1.5
    added_allocation.total_energy_cost_usd = 0.45
    db_session.commit()
    
    # Verify final state
    final_allocation = gpu_repo.get_allocation_by_job_id("test-job-lifecycle")
    assert final_allocation.released_at is not None
    assert final_allocation.total_energy_consumed_kwh == 1.5
    assert final_allocation.total_energy_cost_usd == 0.45 