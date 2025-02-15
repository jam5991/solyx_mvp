from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict
from .models import GPUInstance, GPUAllocation, GPUEnergyUsage


class GPURepository:
    def __init__(self, db: Session):
        self.db = db

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
        self.db.add(gpu)
        self.db.commit()
        self.db.refresh(gpu)
        return gpu

    def update_gpu_price(self, instance_id: str, new_price: float) -> GPUInstance:
        gpu = (
            self.db.query(GPUInstance)
            .filter(GPUInstance.instance_id == instance_id)
            .first()
        )
        if gpu:
            gpu.price_per_hour = new_price
            gpu.last_updated = datetime.utcnow()
            self.db.commit()
            self.db.refresh(gpu)
        return gpu

    def allocate_gpu(self, instance_id: str, job_id: str) -> Optional[GPUAllocation]:
        gpu = (
            self.db.query(GPUInstance)
            .filter(
                GPUInstance.instance_id == instance_id, GPUInstance.available == True
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

        self.db.add(allocation)
        self.db.commit()
        self.db.refresh(allocation)
        return allocation

    def release_gpu(self, instance_id: str) -> bool:
        gpu = (
            self.db.query(GPUInstance)
            .filter(GPUInstance.instance_id == instance_id)
            .first()
        )

        if not gpu:
            return False

        gpu.available = True
        allocation = (
            self.db.query(GPUAllocation)
            .filter(
                GPUAllocation.gpu_instance_id == gpu.id,
                GPUAllocation.released_at == None,
            )
            .first()
        )

        if allocation:
            allocation.released_at = datetime.utcnow()

        self.db.commit()
        return True

    def get_available_gpus(self) -> List[GPUInstance]:
        return self.db.query(GPUInstance).filter(GPUInstance.available == True).all()

    def update_allocation_energy(
        self,
        allocation_id: int,
        energy_consumed_kwh: float,
        energy_cost_usd: float,
        average_power_watts: float,
    ) -> Optional[GPUAllocation]:
        """Update energy usage information for a GPU allocation"""
        allocation = (
            self.db.query(GPUAllocation)
            .filter(GPUAllocation.id == allocation_id)
            .first()
        )

        if allocation:
            allocation.total_energy_consumed_kwh = energy_consumed_kwh
            allocation.total_energy_cost_usd = energy_cost_usd
            allocation.average_power_consumption_watts = average_power_watts
            self.db.commit()
            self.db.refresh(allocation)

        return allocation

    def add_energy_usage(
        self, gpu_instance_id: int, allocation_id: int, energy_data: Dict[str, float]
    ) -> GPUEnergyUsage:
        """Add a detailed energy usage record"""
        energy_usage = GPUEnergyUsage(
            gpu_instance_id=gpu_instance_id,
            allocation_id=allocation_id,
            power_consumption_watts=energy_data["power_consumption_watts"],
            energy_consumed_kwh=energy_data["energy_consumed_kwh"],
            energy_cost_usd=energy_data["energy_cost_usd"],
            energy_rate_kwh=energy_data["energy_rate_kwh"],
        )

        self.db.add(energy_usage)
        self.db.commit()
        self.db.refresh(energy_usage)
        return energy_usage

    def get_energy_usage_by_allocation(
        self, allocation_id: int
    ) -> List[GPUEnergyUsage]:
        """Get all energy usage records for a specific allocation"""
        return (
            self.db.query(GPUEnergyUsage)
            .filter(GPUEnergyUsage.allocation_id == allocation_id)
            .all()
        )

    def get_total_energy_cost(
        self, start_time: datetime, end_time: datetime
    ) -> Dict[str, float]:
        """Get total energy consumption and cost for a time period"""
        allocations = (
            self.db.query(GPUAllocation)
            .filter(
                GPUAllocation.allocated_at >= start_time,
                GPUAllocation.allocated_at <= end_time,
            )
            .all()
        )

        total_energy_kwh = sum(a.total_energy_consumed_kwh or 0 for a in allocations)
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
        gpu_types = self.db.query(GPUInstance.gpu_type).distinct().all()

        for (gpu_type,) in gpu_types:
            allocations = (
                self.db.query(GPUAllocation)
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
                total_cost = sum(a.total_energy_cost_usd or 0 for a in allocations)
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
