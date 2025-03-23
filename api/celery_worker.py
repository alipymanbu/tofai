# celery_worker.py
from celery import Celery
from config import settings

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
    import asyncio
    from services.ai.ai_orchestrator import AIOrchestrator
    
    # Create an event loop
    loop = asyncio.get_event_loop()
    orchestrator = AIOrchestrator()
    
    # For demonstration purposes:
    async def _run_workflow():
        # Get session data
        from services.storage.database import get_db
        db = await get_db()
        session = await db.sessions.find_one({"id": session_id})
        
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Run the workflow
        return await orchestrator.start_generation(
            session_id=session_id,
            brand_framework=session["brand_framework"],
            current_step=current_step
        )
    
    # Run the async workflow in the sync Celery task
    result = loop.run_until_complete(_run_workflow())
    return result