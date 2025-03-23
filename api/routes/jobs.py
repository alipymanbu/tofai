from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime

from app.models.job import JobResponse
from app.utils.database import get_db

router = APIRouter()

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db = Depends(get_db)):
    """Check the status of an asynchronous job."""
    job = await db.jobs.find_one({"id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job

@router.delete("/jobs/{job_id}", status_code=204)
async def cancel_job(job_id: str, db = Depends(get_db)):
    """Cancel a pending or in-progress job."""
    job = await db.jobs.find_one({"id": job_id})
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Can only cancel pending or processing jobs
    if job["status"] not in ["pending", "processing"]:
        raise HTTPException(status_code=400, detail=f"Cannot cancel job in {job['status']} state")
    
    # Update job as canceled
    await db.jobs.update_one(
        {"id": job_id},
        {
            "$set": {
                "status": "failed", 
                "completed_at": datetime.utcnow(),
                "error": "Job canceled by user"
            }
        }
    )
    
    return None

@router.get("/sessions/{session_id}/jobs", response_model=list[JobResponse])
async def list_session_jobs(
    session_id: str, 
    status: Optional[str] = None,
    type: Optional[str] = None,
    limit: int = 10, 
    db = Depends(get_db)
):
    """List all jobs for a session with optional filtering."""
    # Build filter
    filter_query = {"session_id": session_id}
    
    if status:
        filter_query["status"] = status
    
    if type:
        filter_query["type"] = type
    
    # Query jobs
    cursor = db.jobs.find(filter_query).sort("created_at", -1).limit(limit)
    jobs = await cursor.to_list(length=limit)
    
    return jobs