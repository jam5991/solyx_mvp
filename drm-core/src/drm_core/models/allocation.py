from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .base import Base


class GPUAllocation(Base):
    __tablename__ = "gpu_allocations"

    id = Column(Integer, primary_key=True)
    gpu_instance_id = Column(String, ForeignKey("gpu_instances.id"))
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
