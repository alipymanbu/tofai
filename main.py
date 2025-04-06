import asyncio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import sessions, script, strategy, image, speech, music, video, jobs, framework
from services.storage.database import init_db, close_db, seed_mock_data
from config.settings import settings

app = FastAPI(
    title="TOF.ai",
    description="AI-powered video generation platform for brand awareness",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(strategy.router, prefix="/api", tags=["Brand Strategy"])
app.include_router(script.router, prefix="/api", tags=["Script Generation"])
app.include_router(image.router, prefix="/api", tags=["Image Generation"])
app.include_router(speech.router, prefix="/api", tags=["Speech Generation"])
app.include_router(music.router, prefix="/api", tags=["Music Generation"])
app.include_router(video.router, prefix="/api", tags=["Video Generation"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(framework.router, prefix="/api", tags=["Framework"])

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    await init_db()
    
    # Seed mock data if in development environment
    if settings.ENVIRONMENT == "development":
        await seed_mock_data()

@app.on_event("shutdown")
async def shutdown_event():
    """Close connections on shutdown."""
    await close_db()

@app.get("/api/health")
async def health_check():
    """API health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
