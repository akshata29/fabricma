from pydantic import BaseModel


class ChatRequest(BaseModel):
    query: str
    session_id: str
    agent_names: list[str] | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    pattern_used: str | None = None
    agents_used: list[str] = []


class HitlApprovalRequest(BaseModel):
    session_id: str
    approved: bool
    reason: str | None = None
