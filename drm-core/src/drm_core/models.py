from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class GPUInstance(Base):
    __tablename__ = "gpu_instances"

    id = Column(Integer, primary_key=True)
    provider = Column(String)
    instance_id = Column(String)
    gpu_type = Column(String)
    memory_gb = Column(Float)
    price_per_hour = Column(Float)
    region = Column(String)
    available = Column(Boolean, default=True)
    energy_cost_kwh = Column(Float, default=0.12)
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationship with allocation history
    allocations = relationship("GPUAllocation", back_populates="gpu_instance")

    def to_dict(self) -> dict:
        """Convert GPU instance to dictionary"""
        return {
            "id": self.id,
            "provider": self.provider,
            "instance_id": self.instance_id,
            "gpu_type": self.gpu_type,
            "memory_gb": self.memory_gb,
            "price_per_hour": self.price_per_hour,
            "region": self.region,
            "available": self.available,
            "last_updated": self.last_updated.isoformat()
            if self.last_updated
            else None,
        }

    def __repr__(self):
        return (
            f"<GPUInstance(provider='{self.provider}', "
            f"type='{self.gpu_type}', id='{self.instance_id}')>"
        )


class GPUAllocation(Base):
    __tablename__ = "gpu_allocations"

    id = Column(Integer, primary_key=True)
    gpu_instance_id = Column(Integer, ForeignKey("gpu_instances.id"))
    job_id = Column(String)
    allocated_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    price_at_allocation = Column(Float)

    # Energy tracking fields
    total_energy_consumed_kwh = Column(Float, default=0.0)
    total_energy_cost_usd = Column(Float, default=0.0)
    average_power_consumption_watts = Column(Float, default=0.0)

    # Relationship with GPU instance
    gpu_instance = relationship("GPUInstance", back_populates="allocations")

    def __repr__(self):
        return (
            f"<GPUAllocation(job_id='{self.job_id}', "
            f"allocated_at='{self.allocated_at}')>"
        )
