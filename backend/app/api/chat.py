import json

from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.dependencies import AppSettings, CurrentUser
from app.models.chat import ChatRequest, HitlApprovalRequest
from app.services.orchestrator import OrchestratorService
from app.services.session_service import SessionService

router = APIRouter()
_session_service = SessionService()


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: CurrentUser,
    settings: AppSettings,
):
    orchestrator = OrchestratorService(settings, user_token=current_user["token"])

    async def event_generator():
        try:
            async for event in orchestrator.dispatch(request.query, request.session_id):
                yield {"event": event["type"], "data": json.dumps(event["data"])}
        except Exception as exc:
            yield {"event": "error", "data": json.dumps({"message": str(exc)})}

    return EventSourceResponse(event_generator())


@router.post("/chat/hitl")
async def hitl_approval(
    body: HitlApprovalRequest,
    _current_user: CurrentUser,
):
    resolved = _session_service.resolve_hitl(body.session_id, body.approved)
    if not resolved:
        raise HTTPException(status_code=400, detail="No pending HITL for this session")
    return {"status": "resolved", "approved": body.approved}
