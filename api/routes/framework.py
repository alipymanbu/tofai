"""
API routes for framework-driven generation.

NO_AI_CODE=True
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, UTC
import uuid
import logging
import io

from services.storage.database import get_db
from services.ai.tasks.generator import Generator
from services.ai import ai_orchestrator
from services.ai.framework_model import ResultOptions, MediaUri, OutputModality, FrameworkResult, FrameworkStepResult
from services.storage.object_store import upload_bytes
from api.models import GenerateOptionsRequest, GenerateOptionsResponse, JobStatusResponse, InitInputRequest

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/framework/steps/{step_id}/generate", response_model=GenerateOptionsResponse)
async def generate_step_options(
    request: GenerateOptionsRequest,
    session_id: Optional[str] = Query(..., description="Session ID to update"),
    db = Depends(get_db)
):
    """
    Generate options for a framework step.
    
    Args:
        request: The request data including parameters
        session_id: Optional session ID to associate with this generation
        
    Returns:
        Generated options
    """
    start_time = datetime.now(UTC)
    job_id = f"/generate/{request.framework_id}/{request.step_id}/{start_time.strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
    try:
        # Get the session
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        aio = ai_orchestrator.AIOrchestrator(framework_id=request.framework_id)
        result = await aio.run(session=session, current_step_id=request.step_id)

        # Update session with results
        session_update = result
        session_update["updated_at"] = datetime.now(UTC)        
        # Update the session
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": session_update}
        )
        # Update job status
        job = {
            "id": job_id,
            "session_id": session_id,
            "type": "framework_generate",
            "status": "completed",
            "progress": 100,
            "created_at": start_time,
            "completed_at": datetime.now(UTC),
            "result": {
                "step_id": request.step_id,
            }
        }
        await db.jobs.insert_one(job)
        return {
            "message": f"generation success",
            "job_id": job_id,
            "status": "completed",
            "progress": 100
        }
    except Exception as e:
        # Update job status if it exists
        if 'job_id' in locals():
            try:
                await db.jobs.update_one(
                    {"id": job_id},
                    {
                        "$set": {
                            "status": "failed",
                            "progress": 100,
                            "completed_at": datetime.now(UTC),
                            "error": str(e)
                        }
                    }
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")
        raise HTTPException(status_code=500, detail=f"Error generating: {str(e)}")

@router.post("/framework/steps/{step_id}/select", response_model=JobStatusResponse)
async def select_step_option(
    step_id: str,
    framework_id: str,
    session_id: str = Query(..., description="Session ID to update"),
    option_index: int = Query(..., ge=0, description="Index of the selected option"),
    result_index: int = Query(0, ge=0, description="Index of the result group to select from"),
    db = Depends(get_db)
):
    """
    Select an option for a framework step.
    
    Args:
        step_id: The ID of the step
        session_id: Session ID to update
        option_index: Index of the selected option
        result_index: Index of the result group to select from
        
    Returns:
        Job status
    """
    try:
        start_time = datetime.now(UTC)
        # Get the session
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        # Check if framework_result exists
        if not session.get("framework_result"):
            raise HTTPException(status_code=400, detail="Session has no previous generations.")
        framework_result = FrameworkResult.model_validate(session["framework_result"])
        generator = Generator(framework_id=framework_id)
        step = generator.get_step_by_id(step_id=step_id)
        selection_for = generator.get_selection_for_step_id(step_id=step_id)
        if not step or not selection_for:
            raise HTTPException(status_code=400, detail="Invalid step id.")
        is_valid_selection = False
        for step_result in framework_result.step_results:
            if step_result.id == selection_for:
                if result_index < len(step_result.result) and option_index <= len(step_result.result[result_index].result_options):
                    step_result.result[result_index].selected_option = option_index
                    is_valid_selection = True
        if not is_valid_selection:
            raise HTTPException(status_code=404, detail=f"invalid selection")
        
        # Update session with results
        session["framework_result"] = framework_result.model_dump_json()
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {
                "framework_result": session["framework_result"],
                "updated_at": datetime.now(UTC)
            }}
        )
        # Create a job record
        job_id = f"/select/{framework_id}/{step_id}/{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
        job = {
            "id": job_id,
            "session_id": session_id,
            "type": "framework_select",
            "status": "completed",
            "progress": 100,
            "created_at": start_time,
            "completed_at": datetime.now(UTC),
            "result": {
                "step_id": step_id,
                "result_index": result_index,
                "selected_option": option_index
            }
        }
        await db.jobs.insert_one(job)
        
        return {
            "message": f"selection success",
            "job_id": job_id,
            "status": "completed",
            "progress": 100
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")

@router.post("/framework/steps/initial_input", response_model=JobStatusResponse)
async def get_initial_input(
    initial_input: InitInputRequest,
    session_id: str = Query(..., description="Session ID to update"),
    db = Depends(get_db)
):
    """
    Select an option for a framework step.
    
    Args:
        framework_id: The ID of the framework
        session_id: Session ID to update
        
    Returns:
        Job status
    """
    try:
        start_time = datetime.now(UTC)
        # Get the session
        session = await db.sessions.find_one({"id": session_id})
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        generator = Generator(framework_id=initial_input.framework_id)
        step = generator.get_step_by_index(index=0)
        if not step:
            raise HTTPException(status_code=400, detail="Invalid framework id.")
        framework_result = FrameworkResult(
            id=initial_input.framework_id, 
            step_results=[
                FrameworkStepResult(
                    id=step.id,
                     result=[ResultOptions(result_options=[initial_input.brand_link], selected_option=0)]
                )
            ]
        )
        
        # Update session with results
        session["framework_result"] = framework_result.model_dump_json()
        await db.sessions.update_one(
            {"id": session_id},
            {"$set": {
                "framework_result": session["framework_result"],
                "updated_at": datetime.now(UTC)
            }}
        )
        # Create a job record
        job_id = f"/initial_input/{initial_input.framework_id}/{step.id}/{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
        job = {
            "id": job_id,
            "session_id": session_id,
            "type": "framework_initial_input",
            "status": "completed",
            "progress": 100,
            "created_at": start_time,
            "completed_at": datetime.now(UTC),
            "result": {
                "brand_link": initial_input.brand_link
            }
        }
        await db.jobs.insert_one(job)
        
        return {
            "message": f"selection success",
            "job_id": job_id,
            "status": "completed",
            "progress": 100
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")
