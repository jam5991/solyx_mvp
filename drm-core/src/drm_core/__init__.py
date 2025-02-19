"""DRM Core package for managing distributed GPU resources."""
from .config.settings import DRMConfig
from .core import DRMCore
from .models import GPUAllocation, GPUInstance, JobStatus
from .providers import LambdaLabsProvider, VastAIProvider
from .services import JobManager, Scheduler

__version__ = "0.1.0"

__all__ = [
    "DRMCore",
    "DRMConfig",
    "GPUInstance",
    "GPUAllocation",
    "JobStatus",
    "VastAIProvider",
    "LambdaLabsProvider",
    "JobManager",
    "Scheduler",
]
