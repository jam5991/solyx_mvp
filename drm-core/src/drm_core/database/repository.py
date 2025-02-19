import logging
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from ..models import GPUAllocation, GPUInstance

logger = logging.getLogger(__name__)


class GPURepository:
    """Tracks GPU resources and their states"""

    def __init__(self, session: Session):
        self.session = session

    def create_gpu_instance(
        self,
        provider: str,
        instance_id: str,
        gpu_type: str,
        memory_gb: int,
        price_per_hour: float,
        region: str,
        energy_cost_kwh: Optional[float] = None,
    ) -> GPUInstance:
        gpu = GPUInstance(
            provider=provider,
            instance_id=instance_id,
            gpu_type=gpu_type,
            memory_gb=memory_gb,
            price_per_hour=price_per_hour,
            region=region,
            energy_cost_kwh=energy_cost_kwh,
        )
        self.session.add(gpu)
        self.session.commit()
        self.session.refresh(gpu)
        return gpu

    def update_gpu_price(
        self, instance_id: str, new_price: float
    ) -> GPUInstance:
        gpu = (
            self.session.query(GPUInstance)
            .filter(GPUInstance.instance_id == instance_id)
            .first()
        )
        if gpu:
            gpu.price_per_hour = new_price
            gpu.last_updated = datetime.utcnow()
            self.session.commit()
            self.session.refresh(gpu)
        return gpu

    def allocate_gpu(
        self, instance_id: str, job_id: str
    ) -> Optional[GPUAllocation]:
        """Allocate a GPU for a job"""
        gpu = (
            self.session.query(GPUInstance)
            .filter(
                GPUInstance.instance_id == instance_id,
                GPUInstance.available == True,
            )
            .first()
        )

        if not gpu:
            return None

        gpu.available = False
        allocation = GPUAllocation(
            gpu_instance_id=gpu.id,
            job_id=job_id,
            price_at_allocation=gpu.price_per_hour,
        )

        self.session.add(allocation)
        self.session.commit()
        self.session.refresh(allocation)
        return allocation

    def release_gpu(self, job_id: str) -> bool:
        """Release GPU allocation for a given job"""
        try:
            # Find the allocation
            allocation = (
                self.session.query(GPUAllocation)
                .filter(GPUAllocation.job_id == job_id)
                .first()
            )

            if allocation:
                # Update the allocation's released_at timestamp
                allocation.released_at = datetime.utcnow()

                # Mark the GPU as available again
                gpu = (
                    self.session.query(GPUInstance)
                    .filter(GPUInstance.id == allocation.gpu_instance_id)
                    .first()
                )
                if gpu:
                    gpu.available = True

                self.session.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error releasing GPU for job {job_id}: {e}")
            self.session.rollback()
            return False

    def update_allocation_energy(
        self,
        allocation_id: int,
        energy_consumed_kwh: float,
        energy_cost_usd: float,
        average_power_watts: float,
    ) -> Optional[GPUAllocation]:
        """Update energy usage information for a GPU allocation"""
        allocation = (
            self.session.query(GPUAllocation)
            .filter(GPUAllocation.id == allocation_id)
            .first()
        )

        if allocation:
            allocation.total_energy_consumed_kwh = energy_consumed_kwh
            allocation.total_energy_cost_usd = energy_cost_usd
            allocation.average_power_consumption_watts = average_power_watts
            self.session.commit()
            self.session.refresh(allocation)

        return allocation

    def get_total_energy_cost(
        self, start_time: datetime, end_time: datetime
    ) -> Dict[str, float]:
        """Get total energy consumption and cost for a time period"""
        allocations = (
            self.session.query(GPUAllocation)
            .filter(
                GPUAllocation.allocated_at >= start_time,
                GPUAllocation.allocated_at <= end_time,
            )
            .all()
        )

        total_energy_kwh = sum(
            a.total_energy_consumed_kwh or 0 for a in allocations
        )
        total_cost_usd = sum(a.total_energy_cost_usd or 0 for a in allocations)

        return {
            "total_energy_consumed_kwh": total_energy_kwh,
            "total_energy_cost_usd": total_cost_usd,
            "number_of_allocations": len(allocations),
        }

    def get_energy_metrics_by_gpu_type(
        self, start_time: datetime, end_time: datetime
    ) -> List[Dict]:
        """Get energy metrics grouped by GPU type"""
        results = []
        gpu_types = self.session.query(GPUInstance.gpu_type).distinct().all()

        for (gpu_type,) in gpu_types:
            allocations = (
                self.session.query(GPUAllocation)
                .join(GPUInstance)
                .filter(
                    GPUInstance.gpu_type == gpu_type,
                    GPUAllocation.allocated_at >= start_time,
                    GPUAllocation.allocated_at <= end_time,
                )
                .all()
            )

            if allocations:
                total_energy = sum(
                    a.total_energy_consumed_kwh or 0 for a in allocations
                )
                total_cost = sum(
                    a.total_energy_cost_usd or 0 for a in allocations
                )
                avg_power = sum(
                    a.average_power_consumption_watts or 0 for a in allocations
                ) / len(allocations)

                results.append(
                    {
                        "gpu_type": gpu_type,
                        "total_energy_consumed_kwh": total_energy,
                        "total_energy_cost_usd": total_cost,
                        "average_power_watts": avg_power,
                        "number_of_allocations": len(allocations),
                    }
                )

        return results

    def list_available_gpus(self) -> List[GPUInstance]:
        """List all available GPUs"""
        return (
            self.session.query(GPUInstance)
            .filter(GPUInstance.available == True)
            .all()
        )

    def get_gpu_by_id(self, instance_id: str) -> Optional[GPUInstance]:
        """Get a GPU instance by its ID"""
        return (
            self.session.query(GPUInstance)
            .filter(GPUInstance.instance_id == instance_id)
            .first()
        )

    def add_gpu_instance(self, gpu: GPUInstance) -> GPUInstance:
        """Add a new GPU instance or update existing one"""
        existing = (
            self.session.query(GPUInstance)
            .filter_by(provider=gpu.provider, instance_id=gpu.instance_id)
            .first()
        )

        if existing:
            # Update existing instance
            existing.gpu_type = gpu.gpu_type
            existing.memory_gb = gpu.memory_gb
            existing.price_per_hour = gpu.price_per_hour
            existing.region = gpu.region
            existing.available = gpu.available
            existing.last_updated = datetime.utcnow()
            gpu = existing
        else:
            # Add new instance
            self.session.add(gpu)

        self.session.commit()
        return gpu

    def get_gpu_allocations(self, gpu_id: int) -> List[GPUAllocation]:
        """Get allocation history for a GPU"""
        return (
            self.session.query(GPUAllocation)
            .filter_by(gpu_instance_id=gpu_id)
            .all()
        )

    def add_gpu_allocation(self, allocation: GPUAllocation) -> GPUAllocation:
        """Add a new GPU allocation"""
        self.session.add(allocation)
        self.session.commit()
        return allocation

    def get_allocation_by_job_id(self, job_id: str) -> Optional[GPUAllocation]:
        """Get allocation by job ID"""
        return (
            self.session.query(GPUAllocation).filter_by(job_id=job_id).first()
        )
