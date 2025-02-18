from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, validator


class JobType(str, Enum):
    TRAINING = "training"
    INFERENCE = "inference"
    TESTING = "testing"


class JobStatus(str, Enum):
    PENDING = "pending"  # Job submitted but not yet allocated
    ALLOCATED = "allocated"  # GPU allocated, not yet running
    RUNNING = "running"  # Job is running
    COMPLETED = "completed"  # Job finished successfully
    FAILED = "failed"  # Job failed
    CANCELLED = "cancelled"  # Job was cancelled


class JobRequirements(BaseModel):
    """MVP Job Requirements Schema"""

    # Resource Requirements
    required_memory: int = Field(
        ..., gt=0, description="Required GPU memory in GB"
    )
    max_price: Optional[float] = Field(
        None, ge=0.0, description="Maximum price per hour willing to pay"
    )
    provider: Optional[str] = Field(
        None, description="Specific provider request (vastai or lambda)"
    )

    # Job Details
    job_id: str = Field(..., description="Unique identifier for the job")
    job_type: JobType = Field(
        ..., description="Type of job (training, inference, testing)"
    )
    docker_image: str = Field(
        ..., description="Docker image to run (e.g., 'pytorch/pytorch:latest')"
    )
    command: List[str] = Field(
        ..., description="Command to run inside the container"
    )
    env_vars: Optional[Dict[str, str]] = Field(
        default={}, description="Environment variables for the container"
    )

    @validator("provider")
    def validate_provider(cls, v):
        if v and v not in ["vastai", "lambda"]:
            raise ValueError("Provider must be either vastai or lambda")
        return v
