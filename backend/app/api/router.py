from fastapi import APIRouter

from app.api import agents, chat, health, sessions, teams

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(agents.router, prefix="/api/v1", tags=["agents"])
api_router.include_router(sessions.router, prefix="/api/v1", tags=["sessions"])
api_router.include_router(chat.router, prefix="/api/v1", tags=["chat"])
api_router.include_router(teams.router, tags=["teams"])
