from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from drm_core import Scheduler, JobRequirements
from ..database import get_db

router = APIRouter()

@router.post("/")
async def submit_job(
    requirements: JobRequirements,
    scheduler: Scheduler = Depends(get_scheduler),
    db: Session = Depends(get_db)
):
    """Submit a new job"""
    try:
        gpu = await scheduler.select_best_gpu(requirements.dict())
        if not gpu:
            raise HTTPException(
                status_code=404,
                detail="No GPU found matching requirements"
            )
        
        return {
            "status": "success",
            "gpu": gpu.to_dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 