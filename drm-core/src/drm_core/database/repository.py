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
        try:
            # Get the GPU by instance_id
            gpu = (
                self.session.query(GPUInstance)
                .filter(GPUInstance.instance_id == instance_id)
                .first()
            )

            if not gpu or not gpu.available:
                logger.error(f"GPU {instance_id} not available for allocation")
                return None

            # Debug: Print current database state
            logger.info("=== Current Database State ===")
            logger.info(
                f"GPU Instances: {self.session.query(GPUInstance).count()}"
            )
            logger.info(
                f"GPU Allocations: {self.session.query(GPUAllocation).count()}"
            )

            # Create allocation
            allocation = GPUAllocation(
                gpu_instance_id=gpu.id,
                job_id=job_id,
                price_at_allocation=gpu.price_per_hour,
            )

            # Update GPU status
            gpu.available = False
            gpu.status = "allocated"
            gpu.last_updated = datetime.utcnow()

            # Save changes
            self.session.add(allocation)
            self.session.commit()

            # Debug: Print updated database state
            logger.info("=== Updated Database State ===")
            logger.info(
                f"GPU Instances: {self.session.query(GPUInstance).count()}"
            )
            logger.info(
                f"GPU Allocations: {self.session.query(GPUAllocation).count()}"
            )
            logger.info(f"New Allocation: {allocation}")
            logger.info(f"Updated GPU: {gpu}")

            return allocation

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to allocate GPU: {e}")
            return None

    def release_gpu(self, job_id: str) -> bool:
        """Release a GPU allocation for a job"""
        try:
            # Find the allocation
            allocation = self.get_allocation_by_job_id(job_id)
            if not allocation:
                logger.error(f"No allocation found for job {job_id}")
                return False

            # Mark the allocation as released
            allocation.released_at = datetime.utcnow()

            # Mark the GPU as available again
            gpu = self.get_gpu_by_id(allocation.gpu_instance_id)
            if gpu:
                gpu.available = True
                gpu.status = "available"
                gpu.last_updated = datetime.utcnow()

            self.session.commit()
            logger.info(f"Released GPU allocation for job {job_id}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to release GPU for job {job_id}: {e}")
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

    def create_allocation(
        self, job_id: str, instance_id: str
    ) -> Optional[GPUAllocation]:
        """Create and store a new GPU allocation"""
        try:
            # Get the GPU by instance_id
            gpu = (
                self.session.query(GPUInstance)
                .filter(GPUInstance.instance_id == instance_id)
                .first()
            )

            if not gpu:
                logger.error(f"GPU instance {instance_id} not found")
                return None

            # Create new allocation
            allocation = GPUAllocation(
                gpu_instance_id=gpu.id,  # Use the database ID
                job_id=job_id,
                price_at_allocation=gpu.price_per_hour,
            )

            # Mark GPU as unavailable
            gpu.available = False
            gpu.status = "allocated"
            gpu.last_updated = datetime.utcnow()

            # Save changes
            self.session.add(allocation)
            self.session.commit()

            logger.info(f"Created allocation for job {job_id}")
            logger.info(
                f"Status: GPU {gpu.gpu_type} allocated at ${gpu.price_per_hour}/hour"
            )

            return allocation

        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to create allocation: {e}")
            return None

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

    def add_or_update_gpu(self, gpu: GPUInstance) -> None:
        """Add or update a GPU instance in the database"""
        try:
            # Try to find existing GPU by instance_id
            existing = (
                self.session.query(GPUInstance)
                .filter(GPUInstance.instance_id == gpu.instance_id)
                .first()
            )

            if existing:
                # Update existing GPU
                existing.gpu_type = gpu.gpu_type
                existing.memory_gb = gpu.memory_gb
                existing.price_per_hour = gpu.price_per_hour
                existing.region = gpu.region
                existing.available = gpu.available
                existing.status = gpu.status
                logger.info(f"Updated GPU {gpu.instance_id} in database")
            else:
                # Add new GPU
                self.session.add(gpu)
                logger.info(f"Added new GPU {gpu.instance_id} to database")

            self.session.commit()

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error adding/updating GPU {gpu.instance_id}: {e}")
            raise

    def clear_database(self) -> bool:
        """Clear all data from the database"""
        try:
            # Delete all allocations first (due to foreign key constraints)
            self.session.query(GPUAllocation).delete()
            # Then delete all GPU instances
            self.session.query(GPUInstance).delete()
            self.session.commit()
            logger.info("Database cleared successfully")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Failed to clear database: {e}")
            return False

    def get_database_status(self) -> Dict:
        """Get current status of database tables"""
        try:
            gpus = self.session.query(GPUInstance).all()
            allocations = self.session.query(GPUAllocation).all()

            return {
                "gpus": [
                    {
                        "id": g.id,
                        "instance_id": g.instance_id,
                        "available": g.available,
                        "status": g.status,
                    }
                    for g in gpus
                ],
                "allocations": [
                    {
                        "job_id": a.job_id,
                        "gpu_id": a.gpu_instance_id,
                        "allocated_at": a.allocated_at,
                    }
                    for a in allocations
                ],
            }
        except Exception as e:
            logger.error(f"Failed to get database status: {e}")
            return {"error": str(e)}

    def print_database_state(self):
        """Print current state of database tables"""
        try:
            gpus = self.session.query(GPUInstance).all()
            allocations = self.session.query(GPUAllocation).all()

            logger.info("\n=== Database State ===")
            logger.info(f"Total GPUs: {len(gpus)}")
            for gpu in gpus:
                logger.info(
                    f"GPU: {gpu.instance_id} - Status: {gpu.status} - Available: {gpu.available}"
                )

            logger.info(f"\nTotal Allocations: {len(allocations)}")
            for alloc in allocations:
                logger.info(
                    f"Allocation: Job {alloc.job_id} - GPU {alloc.gpu_instance_id}"
                )
            logger.info("=====================")

        except Exception as e:
            logger.error(f"Error getting database state: {e}")
