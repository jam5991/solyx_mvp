import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from drm_core.main import DRMCore
from drm_core.models import Base, GPUInstance
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Test database setup
TEST_DB_PATH = Path(__file__).parent / "test_gpu_tracker.db"
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"


@pytest.fixture(scope="session", autouse=True)
def db_engine():
    """Create database engine"""
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    if TEST_DB_PATH.exists():
        try:
            TEST_DB_PATH.unlink()
        except PermissionError:
            pass


@pytest.fixture(scope="session")
def db_session_factory(db_engine):
    """Create session factory"""
    return scoped_session(sessionmaker(bind=db_engine))


@pytest.fixture
def db_session(db_session_factory):
    """Create a new session for a test"""
    session = db_session_factory()
    yield session
    session.close()


@pytest.fixture(scope="function", autouse=True)
def mock_ray():
    """Mock Ray initialization"""
    with patch("ray.init") as mock_init:
        with patch("ray.shutdown") as mock_shutdown:
            yield {"init": mock_init, "shutdown": mock_shutdown}


@pytest.fixture
def mock_ray_manager():
    """Mock Ray job manager"""
    manager = MagicMock()
    manager.submit_job = AsyncMock(
        return_value={"status": "submitted", "job_id": "test-job"}
    )
    return manager


@pytest.fixture
def sample_gpu(db_session):
    """Create a sample GPU instance"""
    gpu = GPUInstance(
        provider="test_provider",
        instance_id="test-1",
        gpu_type="NVIDIA A100",
        memory_gb=80,
        price_per_hour=2.5,
        region="test-region",
        available=True,
    )
    db_session.add(gpu)
    db_session.commit()
    db_session.refresh(gpu)
    yield gpu


@pytest.fixture
def drm_core(db_engine, mock_ray, mock_ray_manager):
    """Provide DRM Core instance for testing"""
    with patch.dict(
        os.environ,
        {"LAMBDA_API_KEY": "mock_lambda_key", "VAST_API_KEY": "mock_vast_key"},
    ):
        drm = DRMCore(db_url=TEST_DATABASE_URL)
        drm.ray_manager = mock_ray_manager
        yield drm
