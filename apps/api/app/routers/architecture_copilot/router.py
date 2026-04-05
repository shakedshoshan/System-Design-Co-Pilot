from fastapi import APIRouter

from app.routers.architecture_copilot import sessions

router = APIRouter(
    prefix="/api/v1",
    tags=["architecture-co-pilot"],
)

router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
