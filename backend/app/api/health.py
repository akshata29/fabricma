from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/ready")
async def readiness_check():
    settings = get_settings()
    endpoint_preview = settings.azure_ai_project_endpoint[:30] + "..."
    return {"status": "ready", "project": endpoint_preview}
