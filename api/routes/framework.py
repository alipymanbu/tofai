"""
API routes for framework-driven generation.

NO_AI_CODE=True
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timezone
import uuid
import logging
import io

from services.storage.database import DataAccess
from services.ai.tasks.generator import Generator
from services.ai import ai_orchestrator
from services.ai.framework_model import ResultOptions, FrameworkResult, FrameworkStepResult
from api.models import GenerateOptionsRequest, GenerateOptionsResponse, InitInputRequest, JobStatus, Job, UserResponse
from models.job_db import JobDBModel
from api.dependencies import get_data_access

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/framework/steps/{step_id}/generate", response_model=GenerateOptionsResponse)
async def generate_step_options(
    request: GenerateOptionsRequest,
    session_id: Optional[str] = Query(..., description="Session ID to update"),
    db: DataAccess = Depends(get_data_access)
):
    """
    Generate options for a framework step.
    
    Args:
        request: The request data including parameters
        session_id: Optional session ID to associate with this generation
        
    Returns:
        Generated options
    """
    print(f"Arjun: {db}")
    start_time = datetime.now(timezone.utc)
    job_id = f"/generate/{request.framework_id}/{request.step_id}/{start_time.strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
    try:
        # Get the session
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        aio = ai_orchestrator.AIOrchestrator(framework_id=request.framework_id)
        result = await aio.run(session=session.session, current_step_id=request.step_id)

        # Update session with results
        session.session.updated_at = datetime.now(timezone.utc)
        session.session.result = result["framework_result"]
        session.session.current_step_id = result["current_step_id"]        
        await db.update_session(session)
        # Update job status
        job = Job(
            id=job_id,
            session_id=session_id,
            created_at=start_time,
            status=JobStatus.COMPLETED,
            progress=100,
            tasks_completed=[request.step_id]
        )
        await db.insert_job(job_db_model=JobDBModel(job=job))
        return GenerateOptionsResponse(
            message = f"generation success",
            job_id = job_id,
            status = job.status,
            progress = job.progress
        )
    except Exception as e:
        # Update job status if it exists
        if 'job_id' in locals():
            try:
                await db.insert_job(
                    JobDBModel(
                        status = JobStatus.FAILED,
                        progress = 100,
                        completed_at = datetime.now(timezone.utc),
                        error = str(e)
                    )
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")
        raise HTTPException(status_code=500, detail=f"Error generating: {str(e)}")

@router.post("/framework/steps/{step_id}/select", response_model=UserResponse)
async def select_step_option(
    step_id: str,
    framework_id: str,
    session_id: str = Query(..., description="Session ID to update"),
    option_index: int = Query(..., ge=0, description="Index of the selected option"),
    result_index: int = Query(0, ge=0, description="Index of the result group to select from"),
    db: DataAccess = Depends(get_data_access)
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
    print("Arjun: {db}")
    try:
        start_time = datetime.now(timezone.utc)
        # Get the session
        session_db_model = await db.get_session(session_id)
        if not session_db_model:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        # Check if framework_result exists
        if not session_db_model.session.result:
            raise HTTPException(status_code=400, detail="Session has no previous generations.")
        framework_result = session_db_model.session.result
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
        session_db_model.session.result = framework_result
        session_db_model.session.updated_at = datetime.now(timezone.utc)
        await db.update_session(session_db_model)
        # Create a job record
        job_id = f"/select/{framework_id}/{step_id}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
        job = Job(
            id=job_id,
            session_id=session_id,
            created_at=start_time,
            status=JobStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
            progress=100,
            tasks_completed=[step_id],
            result = {
                "step_id": step_id,
                "result_index": result_index,
                "selected_option": option_index
            }
        )
        await db.insert_job(job_db_model=JobDBModel(job=job))
        
        return UserResponse(
            job_id=job.id,
            created_at=job.completed_at,
            framework_id=session_db_model.session.framework_id
        ).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")

@router.post("/framework/steps/initial_input", response_model=UserResponse)
async def get_initial_input(
    initial_input: InitInputRequest,
    session_id: str = Query(..., description="Session ID to update"),
    db: DataAccess = Depends(get_data_access)
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
        start_time = datetime.now(timezone.utc)
        # Get the session
        session_db_model = await db.get_session(session_id)
        if not session_db_model:
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
        session_db_model.session.result = framework_result
        session_db_model.session.updated_at = datetime.now(timezone.utc)
        await db.update_session(session_db_model)
        # Create a job record
        job_id = f"/initial_input/{initial_input.framework_id}/{step.id}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
        job = Job(
            id=job_id,
            session_id=session_id,
            created_at=start_time,
            status=JobStatus.COMPLETED,
            progress=100,
            tasks_completed=[step.id],
            result = {
                "brand_link": initial_input.brand_link
            }
        )
        await db.insert_job(job_db_model=JobDBModel(job=job))
        
        return UserResponse(
            job_id=job.id,
            created_at=job.completed_at,
            framework_id=session_db_model.session.framework_id
        ).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")