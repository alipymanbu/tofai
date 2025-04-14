# Authentication routes package
from fastapi import APIRouter

from api.routes.auth.routes import router as auth_router
from api.routes.auth.admin import router as admin_router

# Combine routers
router = APIRouter()
router.include_router(auth_router)
router.include_router(admin_router, prefix="/admin", tags=["Admin"])