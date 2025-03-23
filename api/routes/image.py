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

class VisualsRequest(BaseModel):
    """Request model for visuals generation."""
    script: Optional[Dict[str, Any]] = None

class VisualScene(BaseModel):
    """Model for a visual scene."""
    sceneNumber: int
    visualUrl: str
    visualType: str = "generated"  # generated, stock, or uploaded

class VisualsResponse(BaseModel):
    """Response model for visuals data."""
    scenes: List[VisualScene]

@router.post("/sessions/{session_id}/visuals")
async def generate_visuals(
    session_id: str,
    request: Optional[VisualsRequest] = None,
    db = Depends(get_db)
):
    """Generate visual concepts based on script."""
    try:
        logger.info(f"Starting visuals generation for session {session_id}")
        
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Get script data
        script_data = None
        if request and request.script:
            script_data = request.script
            logger.info("Using script data from request")
        else:
            script_data = session.get("script")
            if not script_data:
                logger.warning(f"Script not found for session {session_id}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Script must be generated before creating visuals"}
                )
            logger.info("Using script data from session")
        
        # Create a job record to track the generation
        job_id = f"visuals-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        await db.jobs.insert_one({
            "id": job_id,
            "session_id": session_id,
            "type": "visuals",
            "status": "processing",
            "progress": 0,
            "created_at": datetime.utcnow()
        })
        
        # Run the AI orchestrator to generate visuals
        result = await ai_orchestrator.run(session_id, current_step="script")
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Visuals generation failed: {error_msg}")
            
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
            
            return JSONResponse(
                status_code=200,
                content={
                    "error": f"Failed to generate visuals: {error_msg}",
                    "fallback_needed": True
                }
            )
        
        # Get updated session with visuals
        updated_session = await db.sessions.find_one({"id": session_id})
        
        # Use placeholder visuals if not available from orchestrator
        if not updated_session.get("visuals"):
            scenes = script_data.get("scenes", [])
            visual_scenes = []
            
            for i, scene in enumerate(scenes):
                visual_scene = VisualScene(
                    sceneNumber=scene.get("sceneNumber", i + 1),
                    visualUrl=f"/api/placeholder/{(i + 1) * 100}/320",  # Placeholder URLs
                    visualType="generated"
                )
                visual_scenes.append(visual_scene)
            
            visuals_data = {"scenes": visual_scenes}
            
            # Update the session
            await db.sessions.update_one(
                {"id": session_id},
                {
                    "$set": {
                        "visuals": visuals_data,
                        "updated_at": datetime.utcnow(),
                        "current_step": "audio",
                        "status": "visuals"
                    }
                }
            )
        else:
            visuals_data = updated_session.get("visuals")
        
        logger.info(f"Visuals generated successfully for session {session_id}")
        
        # Store visuals in session
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "visuals": visuals_data,
                    "updated_at": datetime.utcnow(),
                    "current_step": "audio",  # Update current step
                    "status": "visuals"  # Update status
                }
            }
        )
        
        # Update job status
        await db.jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "progress": 100,
                    "completed_at": datetime.utcnow(),
                    "result": visuals_data
                }
            }
        )
        
        # Return the job ID and the visuals data for immediate use
        return {
            "id": job_id,
            "type": "visuals",
            "status": "completed",
            "session_id": session_id,
            "visuals": visuals_data  # Include the data immediately
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error in visuals generation: {str(e)}")
        return JSONResponse(
            status_code=200,  # Use 200 status with error data to avoid frontend crash
            content={
                "error": str(e),
                "fallback_needed": True
            }
        )

@router.get("/sessions/{session_id}/visuals", response_model=Optional[VisualsResponse])
async def get_visuals(
    session_id: str,
    db = Depends(get_db)
):
    """Get generated visuals for the session."""
    try:
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Get visuals data
        visuals = session.get("visuals")
        
        if not visuals:
            logger.warning(f"Visuals not found for session {session_id}")
            return JSONResponse(
                status_code=404,
                content={"error": "Visuals not found"}
            )
        
        return visuals
    
    except Exception as e:
        logger.exception(f"Unexpected error retrieving visuals: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={"error": str(e)}
        )