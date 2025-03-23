from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from services.storage.database import get_db
from app.services.ai.gemini_client_fixed import GeminiClient

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize Gemini client
gemini_client = GeminiClient()

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
        
        # Get strategy data
        strategy_data = None
        if request and request.strategy:
            strategy_data = request.strategy
            logger.info("Using strategy data from request")
        else:
            strategy_data = session.get("strategy")
            if not strategy_data:
                logger.warning(f"Strategy not found for session {session_id}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Strategy must be generated before creating a script"}
                )
            logger.info("Using strategy data from session")
        
        # Call Gemini to generate script
        logger.info(f"Generating script with strategy: {strategy_data}")
        script_result = await gemini_client.generate_script(strategy_data)
        
        if not script_result["success"]:
            error_msg = script_result.get("error", "Unknown error")
            logger.error(f"Script generation failed: {error_msg}")
            
            # Return error but with 200 status to avoid frontend crash
            return JSONResponse(
                status_code=200,
                content={
                    "error": f"Failed to generate script: {error_msg}",
                    "fallback_needed": True
                }
            )
        
        script_data = script_result["script"]
        logger.info(f"Script generated successfully for session {session_id}")
        
        # Store script in session
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "script": script_data,
                    "updated_at": datetime.utcnow(),
                    "current_step": "visuals",  # Update current step
                    "status": "script"  # Update status
                }
            }
        )
        
        # Create a job record to track the generation
        job_id = f"script-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        await db.jobs.insert_one({
            "id": job_id,
            "session_id": session_id,
            "type": "script",
            "status": "completed",
            "progress": 100,
            "created_at": datetime.utcnow(),
            "completed_at": datetime.utcnow(),
            "result": script_data
        })
        
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