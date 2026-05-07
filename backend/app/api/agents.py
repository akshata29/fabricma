from fastapi import APIRouter

from app.dependencies import AppSettings, CurrentUser
from app.models.agent import AgentListResponse
from app.services.agent_service import list_agents

router = APIRouter()


@router.get("/agents", response_model=AgentListResponse)
async def get_agents(
    settings: AppSettings,
    _current_user: CurrentUser,
) -> AgentListResponse:
    return AgentListResponse(agents=list_agents(settings))
