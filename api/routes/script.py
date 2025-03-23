from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.storage.database import get_db
from services.ai.ai_orchestrator import AIOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize AI orchestrator
ai_orchestrator = AIOrchestrator()

class ScriptRequest(BaseModel):
    """Request model for script generation."""
    strategy: Optional[Dict[str, Any]] = None

class SceneModel(BaseModel):
    """Model for a script scene."""
    sceneNumber: int
    narration: str
    visualDescription: str
    duration: int

class ScriptResponse(BaseModel):
    """Response model for script data."""
    scenes: List[SceneModel]
    totalDuration: int

@router.post("/sessions/{session_id}/script")
async def generate_script(
    session_id: str,
    request: Optional[ScriptRequest] = None,
    db = Depends(get_db)
):
    """Generate video script based on strategy."""
    try:
        logger.info(f"Starting script generation for session {session_id}")
        
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Check if strategy exists
        if not session.get("strategy"):
            logger.warning(f"Strategy not found for session {session_id}")
            return JSONResponse(
                status_code=400,
                content={"error": "Strategy must be generated before creating a script"}
            )
        
        # Create a job record to track the generation
        job_id = f"script-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        await db.jobs.insert_one({
            "id": job_id,
            "session_id": session_id,
            "type": "script",
            "status": "processing",
            "progress": 0,
            "created_at": datetime.utcnow()
        })
        
        # Run the AI orchestrator to generate script
        result = await ai_orchestrator.run(session_id, current_step="strategy")
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Script generation failed: {error_msg}")
            
            # Update job status
            await db.jobs.update_one(
                {"id": job_id},
                {
                    "$set": {
                        "status": "failed",
                        "progress": 100,
                        "completed_at": datetime.utcnow(),
                        "error": error_msg
                    }
                }
            )
            
            # Return error but with 200 status to avoid frontend crash
            return JSONResponse(
                status_code=200,
                content={
                    "error": f"Failed to generate script: {error_msg}",
                    "fallback_needed": True
                }
            )
        
        # Get updated session with script
        updated_session = await db.sessions.find_one({"id": session_id})
        script_data = updated_session.get("script", {})
        
        # Update job status
        await db.jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "progress": 100,
                    "completed_at": datetime.utcnow(),
                    "result": script_data
                }
            }
        )
        
        # Return the job ID and the script data for immediate use
        return {
            "id": job_id,
            "type": "script",
            "status": "completed",
            "session_id": session_id,
            "script": script_data  # Include the data immediately
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error in script generation: {str(e)}")
        
        # Update job status if job was created
        if 'job_id' in locals():
            try:
                await db.jobs.update_one(
                    {"id": job_id},
                    {
                        "$set": {
                            "status": "failed",
                            "progress": 100,
                            "completed_at": datetime.utcnow(),
                            "error": str(e)
                        }
                    }
                )
            except Exception as update_error:
                logger.error(f"Failed to update job status: {update_error}")
        
        return JSONResponse(
            status_code=200,  # Use 200 status with error data to avoid frontend crash
            content={
                "error": str(e),
                "fallback_needed": True
            }
        )

@router.get("/sessions/{session_id}/script", response_model=Optional[ScriptResponse])
async def get_script(
    session_id: str,
    db = Depends(get_db)
):
    """Get generated script for the session."""
    try:
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Get script data
        script = session.get("script")
        
        if not script:
            logger.warning(f"Script not found for session {session_id}")
            return JSONResponse(
                status_code=404,
                content={"error": "Script not found"}
            )
        
        return script
    
    except Exception as e:
        logger.exception(f"Unexpected error retrieving script: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={"error": str(e)}
        )

@router.put("/sessions/{session_id}/script")
async def update_script(
    session_id: str,
    script: ScriptResponse,
    db = Depends(get_db)
):
    """Update script for the session."""
    try:
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Update script
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "script": dict(script),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Script updated successfully"}
    
    except Exception as e:
        logger.exception(f"Unexpected error updating script: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={"error": str(e)}
        )
