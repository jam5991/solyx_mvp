from enum import Enum
from typing import Optional

from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobRequirements(BaseModel):
    min_memory: Optional[float] = None
    max_price: Optional[float] = None
    gpu_type: Optional[str] = None
    provider: Optional[str] = None
