from fastapi import APIRouter

router = APIRouter(
    prefix="/api/v1",
    tags=["architecture-co-pilot"],
)

# Include domain routers, e.g.:
# from app.routers.architecture_copilot import sessions
# router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
