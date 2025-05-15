import asyncio
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from api.middleware.auth_middleware import AuthMiddleware

from api.routes import sessions, jobs, framework, feedback
from api.routes.auth import router as auth_router
from services.storage.database import DataAccess
from config.settings import settings
from api.dependency.data import initialize_data_access, get_data_access

data_access_instance: Optional[DataAccess] = None

async def startup_event():
    """Initialize services on startup."""
    await initialize_data_access()

async def shutdown_event():
    """Close connections on shutdown."""
    # if data_access_instance:
    #     await data_access_instance.mongo_client.close()
    #     await data_access_instance.redis_client.close()
    pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    await startup_event()
    yield
    await shutdown_event()

app = FastAPI(
    title="TOF.ai",
    description="AI-powered video generation platform for brand awareness",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://tofai-frontend.web.app"],  # Specify exact origins instead of wildcard "*"
    allow_credentials=True,  # This is crucial
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)


# Register API routes with the dependency
app.include_router(sessions.router, prefix="/api", tags=["Sessions"])
app.include_router(jobs.router, prefix="/api", tags=["Jobs"])
app.include_router(framework.router, prefix="/api", tags=["Framework"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(feedback.router, prefix="/api", tags=["Feedback"])

@app.get("/api/health")
async def health_check(db: DataAccess = Depends(get_data_access)):
    """API health check endpoint."""
    return {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "database_initialized": db is not None
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )