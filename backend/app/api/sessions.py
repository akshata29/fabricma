from fastapi import APIRouter, HTTPException

from app.dependencies import CurrentUser
from app.models.session import SessionCreate, SessionResponse
from app.services.session_service import SessionService

router = APIRouter()
_session_service = SessionService()


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    body: SessionCreate,
    _current_user: CurrentUser,
) -> SessionResponse:
    state = _session_service.create_session(agent_name=body.agent_name)
    return SessionResponse(
        session_id=state.session_id,
        created_at=state.created_at,
        agent_name=state.agent_name,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, _current_user: CurrentUser) -> SessionResponse:
    state = _session_service.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionResponse(
        session_id=state.session_id,
        created_at=state.created_at,
        agent_name=state.agent_name,
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(session_id: str, _current_user: CurrentUser) -> None:
    deleted = _session_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
