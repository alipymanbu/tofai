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
from services.ai.framework_model import ResultOptions, FrameworkResult, FrameworkStepResult, FrameworkStep
from api.models import GenerateOptionsRequest, GenerateOptionsResponse, InitInputRequest, JobStatus, Job, UserResponse, SelectRequest
from models.job_db import JobDBModel
from api.dependency.data import get_data_access
from api.dependency.auth import get_current_user
from api.models import User

logger = logging.getLogger(__name__)
router = APIRouter()

def _get_next_api_call(step: Optional[FrameworkStep], generator: Generator) -> tuple[Optional[str], bool]:
    """
    Get the next API call based on the next step from the framework.
    
    Args:
        step: The framework step
        
    Returns:
        The next API call or None
    """
    next_step = generator.get_step_by_id(step_id=step.id)
    if next_step:
        if next_step.requires_user_input:
            return f"/api/framework/steps/{next_step.next_step}/generate", False
        else:
            return f"/api/framework/steps/{next_step.next_step}/select", True
    return None, True

@router.post("/framework/steps/{step_id}/generate", response_model=GenerateOptionsResponse)
async def generate_step_options(
    request: GenerateOptionsRequest,
    session_id: Optional[str] = Query(..., description="Session ID to update"),
    user: User = Depends(get_current_user),
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
    start_time = datetime.now(timezone.utc)
    job_id = f"/generate/{request.framework_id}/{request.step_id}/{start_time.strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
    try:
        # Get the session
        session = await db.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        generator = Generator(framework_id=request.framework_id)
        aio = ai_orchestrator.AIOrchestrator(framework_id=request.framework_id)
        result = await aio.run(session=session.session, current_step_id=request.step_id)
        # Update session with results
        session.session.updated_at = datetime.now(timezone.utc)
        session.session.result = result["framework_result"]
        session.session.current_step_id = result["current_step_id"]
        latest_step = generator.get_step_by_id(step_id=session.session.current_step_id)
        if not latest_step:
            next_api_call, wait_for_user_action = None, True
        else:
            next_api_call, wait_for_user_action = _get_next_api_call(latest_step, generator)     
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
            framework_id=request.framework_id,
            step_id=request.step_id,
            job_id = job_id,
            status = job.status,
            created_at = job.created_at,
            progress = job.progress,
            next_api = next_api_call,
            wait_for_user_action = wait_for_user_action
        )
    except Exception as e:
        # Update job status if it exists
        if 'job_id' in locals():
            try:
                await db.insert_job(
                    JobDBModel(
                        job=Job(
                            id=f"error-{uuid.uuid4().hex}",
                            session_id=session_id,
                            status = JobStatus.FAILED,
                            progress = 100,
                            created_at = datetime.now(timezone.utc),
                            error = str(e)
                        )
                    )
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {str(update_error)}")
        raise HTTPException(status_code=500, detail=f"Error generating: {str(e)}")

@router.post("/framework/steps/{step_id}/select", response_model=UserResponse)
async def select_step_option(
    request: SelectRequest,
    session_id: str = Query(..., description="Session ID to update"),
    user: User = Depends(get_current_user),
    db: DataAccess = Depends(get_data_access)
):
    """
    Select an option for a framework step.
    
    Args:
        request: The request data including parameters
        session_id: Session ID to update
        
    Returns:
        Job status
    """
    try:
        start_time = datetime.now(timezone.utc)
        # Get the session
        session_db_model = await db.get_session(session_id)
        print(f"Session from storage: {session_db_model}")
        if not session_db_model:
            raise HTTPException(status_code=404, detail=f"Session not found: {session_id}")
        # Check if framework_result exists
        if not session_db_model.session.result:
            raise HTTPException(status_code=400, detail="Session has no previous generations.")
        framework_result = session_db_model.session.result
        generator = Generator(framework_id=request.framework_id)
        step = generator.get_step_by_id(step_id=request.step_id)
        selection_step = generator.get_step_id_for_selection_id(step_id=request.step_id)
        next_api_call, wait_for_user_action = _get_next_api_call(selection_step, generator)
        print(f"Selection for: {selection_step} {request}")
        if not step or not selection_step:
            raise HTTPException(status_code=400, detail="Invalid step id.")
        is_valid_selection = False
        for step_result in framework_result.step_results:
            if step_result.id == step.id:
                if request.result_index < len(step_result.result) and request.option_index <= len(step_result.result[request.result_index].result_options):
                    step_result.result[request.result_index].selected_option = request.option_index
                    is_valid_selection = True
        if not is_valid_selection:
            raise HTTPException(status_code=404, detail=f"invalid selection")
        
        # Update session with results
        session_db_model.session.result = framework_result
        session_db_model.session.updated_at = datetime.now(timezone.utc)
        await db.update_session(session_db_model)
        # Create a job record
        job_id = f"/select/{request.framework_id}/{request.step_id}/{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}/{str(uuid.uuid4())}"
        job = Job(
            id=job_id,
            session_id=session_id,
            created_at=start_time,
            status=JobStatus.COMPLETED,
            completed_at=datetime.now(timezone.utc),
            progress=100,
            tasks_completed=[request.step_id],
            result = {
                "step_id": request.step_id,
                "result_index": request.result_index,
                "selected_option": request.option_index
            }
        )
        await db.insert_job(job_db_model=JobDBModel(job=job))
        
        return UserResponse(
            job_id=job.id,
            created_at=job.completed_at,
            framework_id=session_db_model.session.framework_id,
            next_api = next_api_call,
            wait_for_user_action = wait_for_user_action
        ).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")

@router.post("/framework/steps/initial_input", response_model=UserResponse)
async def get_initial_input(
    initial_input: InitInputRequest,
    session_id: str = Query(..., description="Session ID to update"),
    user: User = Depends(get_current_user),
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
        next_api_call, wait_for_user_action = _get_next_api_call(step, generator)
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
            created_at=job.created_at,
            framework_id=session_db_model.session.framework_id,
            next_api = next_api_call,
            wait_for_user_action = wait_for_user_action
        ).model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting option: {str(e)}")