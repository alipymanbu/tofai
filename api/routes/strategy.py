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

class StrategyRequest(BaseModel):
    """Request model for strategy generation."""
    brand_data: Optional[Dict[str, Any]] = None

class StrategyResponse(BaseModel):
    """Response model for strategy data."""
    content_theme: str
    key_messages: List[str]
    recommended_length: str
    call_to_action: str

@router.post("/sessions/{session_id}/strategy")
async def generate_strategy(
    session_id: str,
    request: Optional[StrategyRequest] = None,
    db = Depends(get_db)
):
    """Generate content strategy based on brand framework."""
    try:
        logger.info(f"Starting strategy generation for session {session_id}")
        
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Get brand framework data
        brand_framework = session.get("brand_framework", {})
        if not brand_framework:
            logger.warning(f"Brand framework not found for session {session_id}")
            return JSONResponse(
                status_code=400, 
                content={"error": "Brand framework must be completed before generating strategy"}
            )
        
        # Create a job record to track the generation
        job_id = f"strategy-{session_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        await db.jobs.insert_one({
            "id": job_id,
            "session_id": session_id,
            "type": "strategy",
            "status": "processing",
            "progress": 0,
            "created_at": datetime.utcnow()
        })
        
        # Run the AI orchestrator to generate strategy
        result = await ai_orchestrator.run(session_id, current_step="brand-framework")
        
        if not result["success"]:
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Strategy generation failed: {error_msg}")
            
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
                    "error": f"Failed to generate strategy: {error_msg}",
                    "fallback_needed": True
                }
            )
        
        # Get updated session with strategy
        updated_session = await db.sessions.find_one({"id": session_id})
        strategy_data = updated_session.get("strategy", {})
        
        # Update job status
        await db.jobs.update_one(
            {"id": job_id},
            {
                "$set": {
                    "status": "completed",
                    "progress": 100,
                    "completed_at": datetime.utcnow(),
                    "result": strategy_data
                }
            }
        )
        
        # Return the job ID and the strategy data for immediate use
        return {
            "id": job_id,
            "type": "strategy",
            "status": "completed",
            "session_id": session_id,
            "strategy": strategy_data  # Include the data immediately
        }
    
    except Exception as e:
        logger.exception(f"Unexpected error in strategy generation: {str(e)}")
        
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

@router.get("/sessions/{session_id}/strategy", response_model=Optional[StrategyResponse])
async def get_strategy(
    session_id: str,
    db = Depends(get_db)
):
    """Get generated strategy for the session."""
    try:
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Get strategy data
        strategy = session.get("strategy")
        
        if not strategy:
            logger.warning(f"Strategy not found for session {session_id}")
            return JSONResponse(
                status_code=404,
                content={"error": "Strategy not found"}
            )
        
        return strategy
    
    except Exception as e:
        logger.exception(f"Unexpected error retrieving strategy: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={"error": str(e)}
        )

@router.put("/sessions/{session_id}/strategy")
async def update_strategy(
    session_id: str,
    strategy: StrategyResponse,
    db = Depends(get_db)
):
    """Update strategy for the session."""
    try:
        # Check if session exists
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.warning(f"Session {session_id} not found")
            return JSONResponse(
                status_code=404,
                content={"error": "Session not found"}
            )
        
        # Update strategy
        await db.sessions.update_one(
            {"id": session_id},
            {
                "$set": {
                    "strategy": dict(strategy),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"message": "Strategy updated successfully"}
    
    except Exception as e:
        logger.exception(f"Unexpected error updating strategy: {str(e)}")
        return JSONResponse(
            status_code=200,
            content={"error": str(e)}
        )

@router.post("/sessions/{session_id}/strategy/regenerate")
async def regenerate_strategy(
    session_id: str,
    request: Optional[StrategyRequest] = None,
    db = Depends(get_db)
):
    """Regenerate content strategy."""
    # Reusing the generate_strategy logic
    return await generate_strategy(session_id, request, db)
