from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, String
from sqlalchemy.orm import relationship

from .base import Base


class GPUInstance(Base):
    __tablename__ = "gpu_instances"

    id = Column(String, primary_key=True)
    provider = Column(String, nullable=False)
    instance_id = Column(String)
    gpu_type = Column(String, nullable=False)
    memory_gb = Column(Float, nullable=False)
    price_per_hour = Column(Float, nullable=False)
    region = Column(String)
    available = Column(Boolean, default=True)
    energy_cost_kwh = Column(Float, default=0.12)
    status = Column(String, default="available")
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Add relationship to allocations
    allocations = relationship("GPUAllocation", back_populates="gpu_instance")

    def __repr__(self):
        return f"<GPUInstance(id={self.id}, type={self.gpu_type}, memory={self.memory_gb}GB)>"

    def to_dict(self):
        return {
            "id": self.id,
            "provider": self.provider,
            "instance_id": self.instance_id,
            "gpu_type": self.gpu_type,
            "memory_gb": self.memory_gb,
            "price_per_hour": self.price_per_hour,
            "region": self.region,
            "status": self.status,
            "available": self.available,
            "last_updated": self.last_updated,
        }
