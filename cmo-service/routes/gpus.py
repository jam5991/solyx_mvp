from drm_core import Scheduler
from fastapi import APIRouter, Depends

router = APIRouter()


@router.get("/summary")
async def gpu_summary(
    scheduler: Scheduler = Depends(get_scheduler), provider: str = None
):
    """Get summary of available GPUs"""
    return await scheduler.get_gpu_summary(provider)
