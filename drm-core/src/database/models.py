from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class GPUInstance(Base):
    __tablename__ = "gpu_instances"

    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=False)  # vast.ai, coreweave, etc.
    instance_id = Column(String, nullable=False)
    gpu_type = Column(String, nullable=False)  # A100, V100, etc.
    memory_gb = Column(Integer, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    region = Column(String, nullable=False)
    available = Column(Boolean, default=True)
    energy_cost_kwh = Column(Float)  # Energy cost in the region
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship with allocation history
    allocations = relationship("GPUAllocation", back_populates="gpu_instance")

    def __repr__(self):
        return f"<GPUInstance(provider='{self.provider}', gpu_type='{self.gpu_type}')>"


class GPUAllocation(Base):
    __tablename__ = "gpu_allocations"

    id = Column(Integer, primary_key=True)
    gpu_instance_id = Column(Integer, ForeignKey("gpu_instances.id"))
    job_id = Column(String, nullable=False)
    allocated_at = Column(DateTime, default=datetime.utcnow)
    released_at = Column(DateTime, nullable=True)
    price_at_allocation = Column(Float, nullable=False)

    # Add energy tracking fields
    total_energy_consumed_kwh = Column(Float, nullable=True)
    total_energy_cost_usd = Column(Float, nullable=True)
    average_power_consumption_watts = Column(Float, nullable=True)

    # Relationship with GPU instance
    gpu_instance = relationship("GPUInstance", back_populates="allocations")

    def __repr__(self):
        return f"<GPUAllocation(job_id='{self.job_id}', allocated_at='{self.allocated_at}')>"


class GPUEnergyUsage(Base):
    __tablename__ = "gpu_energy_usage"

    id = Column(Integer, primary_key=True)
    gpu_instance_id = Column(Integer, ForeignKey("gpu_instances.id"))
    allocation_id = Column(Integer, ForeignKey("gpu_allocations.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    power_consumption_watts = Column(Float)
    energy_consumed_kwh = Column(Float)
    energy_cost_usd = Column(Float)
    energy_rate_kwh = Column(Float)
