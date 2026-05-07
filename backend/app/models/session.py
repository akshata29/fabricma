from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    agent_name: str | None = None


class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    agent_name: str | None = None
