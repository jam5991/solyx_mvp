#!/usr/bin/env python3
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from drm_core.database.models import Base, GPUInstance, GPUAllocation, GPUEnergyUsage
from tabulate import tabulate
import json
from datetime import datetime

def view_job_activity():
    """View all job scheduling activity and GPU allocations"""
    # Setup database connection
    db_path = Path(__file__).parent.parent.parent / "test_gpu_tracker.db"
    if not db_path.exists():
        print(f"Database not found at: {db_path}")
        return

    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Query allocations with GPU information
        allocations = session.query(
            GPUAllocation, GPUInstance
        ).join(
            GPUInstance, GPUAllocation.gpu_instance_id == GPUInstance.id
        ).all()

        if not allocations:
            print("\n⚠️  No job activity found in database!")
            return

        # Prepare data for display
        job_data = []
        for allocation, gpu in allocations:
            try:
                region = json.loads(gpu.region) if gpu.region.startswith('{') else gpu.region
            except:
                region = gpu.region

            job_data.append([
                allocation.job_id,
                allocation.status,
                gpu.gpu_type,
                f"{gpu.memory_gb}GB",
                f"${gpu.price_per_hour:.2f}/hr",
                region,
                allocation.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                allocation.updated_at.strftime("%Y-%m-%d %H:%M:%S") if allocation.updated_at else "N/A"
            ])

        # Display job activity
        headers = ["Job ID", "Status", "GPU Type", "Memory", "Price", "Region", "Started", "Updated"]
        print("\n🚀 Job Scheduling Activity:")
        print(tabulate(job_data, headers=headers, tablefmt="pretty"))

        # Display summary statistics
        total_jobs = len(allocations)
        completed_jobs = sum(1 for alloc, _ in allocations if alloc.status == "completed")
        active_jobs = sum(1 for alloc, _ in allocations if alloc.status == "active")
        failed_jobs = sum(1 for alloc, _ in allocations if alloc.status == "failed")

        print("\n📊 Summary Statistics:")
        print(f"Total Jobs: {total_jobs}")
        print(f"Completed Jobs: {completed_jobs}")
        print(f"Active Jobs: {active_jobs}")
        print(f"Failed Jobs: {failed_jobs}")

        # Display GPU utilization
        gpus = session.query(GPUInstance).all()
        print("\n💻 GPU Utilization:")
        for gpu in gpus:
            active_allocs = session.query(GPUAllocation).filter(
                GPUAllocation.gpu_instance_id == gpu.id,
                GPUAllocation.status == "active"
            ).count()
            
            print(f"\nGPU: {gpu.gpu_type} ({gpu.instance_id})")
            print(f"- Active Jobs: {active_allocs}")
            print(f"- Available: {'✅' if gpu.available else '❌'}")
            print(f"- Price: ${gpu.price_per_hour:.2f}/hr")

    except Exception as e:
        print(f"Error viewing job activity: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    view_job_activity() 