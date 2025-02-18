import pytest
from unittest.mock import AsyncMock, patch
from drm_core.models import GPUInstance

@pytest.fixture
def mock_providers():
    """Mock GPU providers"""
    sample_gpus = [
        GPUInstance(
            provider="test_provider",
            instance_id="test-1",
            gpu_type="NVIDIA A100",
            memory_gb=80,
            price_per_hour=2.5,
            region="test-region",
            available=True
        )
    ]

    mock_vast = AsyncMock()
    mock_lambda = AsyncMock()
    
    mock_vast.list_available_gpus = AsyncMock(return_value=sample_gpus)
    mock_lambda.list_available_gpus = AsyncMock(return_value=sample_gpus)
    
    with patch('drm_core.main.VastAIProvider', return_value=mock_vast):
        with patch('drm_core.main.LambdaLabsProvider', return_value=mock_lambda):
            yield {
                'vast': mock_vast,
                'lambda': mock_lambda
            }

@pytest.mark.asyncio
async def test_provider_initialization(drm_core, mock_providers):
    """Test provider initialization and GPU fetching"""
    gpus = await drm_core.initialize_providers()
    assert isinstance(gpus, list)
    assert len(gpus) == 2  # One from each provider
    
    mock_providers['vast'].list_available_gpus.assert_called_once()
    mock_providers['lambda'].list_available_gpus.assert_called_once()

@pytest.mark.asyncio
async def test_provider_error_handling(drm_core, mock_providers):
    """Test provider error handling"""
    mock_providers['vast'].list_available_gpus.side_effect = Exception("API Error")
    
    gpus = await drm_core.initialize_providers()
    assert isinstance(gpus, list)
    assert len(gpus) == 1  # Only Lambda provider succeeded 