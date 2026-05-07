import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

_SESSION_TTL = timedelta(hours=2)


@dataclass
class SessionState:
    session_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))
    agent_name: str | None = None
    hitl_pending: dict[str, Any] | None = None


class SessionService:
    _store: dict[str, SessionState] = {}

    def _evict_expired(self) -> None:
        now = datetime.now(tz=timezone.utc)
        expired = [
            sid for sid, state in SessionService._store.items()
            if now - state.created_at > _SESSION_TTL
        ]
        for sid in expired:
            del SessionService._store[sid]

    def create_session(self, agent_name: str | None = None) -> SessionState:
        self._evict_expired()
        session_id = str(uuid.uuid4())
        state = SessionState(session_id=session_id, agent_name=agent_name)
        SessionService._store[session_id] = state
        return state

    def get_session(self, session_id: str) -> SessionState | None:
        return SessionService._store.get(session_id)

    def store_hitl_pending(self, session_id: str, hitl_data: dict) -> None:
        if session_id in SessionService._store:
            SessionService._store[session_id].hitl_pending = hitl_data

    def delete_session(self, session_id: str) -> bool:
        if session_id in SessionService._store:
            del SessionService._store[session_id]
            return True
        return False

    def resolve_hitl(self, session_id: str, approved: bool) -> bool:
        state = SessionService._store.get(session_id)
        if state and state.hitl_pending is not None:
            state.hitl_pending = None
            return True
        return False
