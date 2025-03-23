# celery_worker.py
from celery import Celery
from config.settings import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

celery_app = Celery(
    "tofai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

@celery_app.task
def run_generation_workflow(session_id: str, current_step: str):
    """Run the content generation workflow as a Celery task."""
    from services.ai.ai_orchestrator import AIOrchestrator
    
    # Create an event loop for the async code
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # If there's no event loop in this thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    orchestrator = AIOrchestrator()
    
    async def _run_workflow():
        # Initialize DB connection
        from services.storage.database import init_db, get_db
        await init_db()
        
        # Get session data
        db = await get_db()
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            logger.error(f"Session {session_id} not found")
            raise ValueError(f"Session {session_id} not found")
        
        brand_framework = session.get("brand_framework", {})
        
        # Run the generation workflow
        result = await orchestrator.start_generation(
            session_id=session_id,
            brand_framework=brand_framework,
            current_step=current_step
        )
        
        # Close DB connection
        from services.storage.database import close_db
        await close_db()
        
        return result
    
    # Run the async workflow in the sync Celery task
    try:
        result = loop.run_until_complete(_run_workflow())
        return result
    except Exception as e:
        logger.exception(f"Error in generation workflow: {str(e)}")
        return {"error": str(e)}
    finally:
        # Clean up the loop
        loop.close()