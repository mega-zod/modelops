from fastapi import APIRouter, Depends

from app.api.routes import chat, demo, deployments, health
from app.api.security import require_api_key

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"],
    dependencies=[Depends(require_api_key)],
)
api_router.include_router(
    demo.router,
    prefix="/demo",
    tags=["demo"],
    dependencies=[Depends(require_api_key)],
)
api_router.include_router(
    deployments.router,
    prefix="/deployments",
    tags=["deployments"],
    dependencies=[Depends(require_api_key)],
)
