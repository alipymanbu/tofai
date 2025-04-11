from fastapi import APIRouter, HTTPException, Depends, status
from typing import Optional, List
from datetime import datetime, timezone
import logging

from services.storage.database import DataAccess
from api.models import Job
from api.dependencies import get_data_access

router = APIRouter()
logger = logging.getLogger(__name__)

class JobResponse(Job):
    pass

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db: DataAccess = Depends(get_data_access)):
    """Check the status of an asynchronous job."""
    try:
        job_db_model = await db.get_job(job_id)
        if not job_db_model:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        return job_db_model.job
    except Exception as e:
        logger.error(f"Error getting job {job_id} with exception: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error getting job status.")
