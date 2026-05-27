"""FastAPI route for the Bot Framework /api/messages endpoint.

Azure Bot Service (and the Teams channel) POST every incoming activity to this
endpoint.  BotFrameworkAdapter handles:
  - JWT validation of the Bot Framework token (separate from the Entra user JWT
    used by the SPA routes)
  - Serialising the Activity from the request body
  - Calling MeridianTeamsBot.on_turn() with the enriched TurnContext
  - Serialising and returning the response to Azure Bot Service

The endpoint is only active when TEAMS_APP_ID and TEAMS_APP_PASSWORD are set in
.env.  In development you can leave them empty and the adapter runs in
unauthenticated mode (suitable for local Bot Framework Emulator testing).
"""

from __future__ import annotations

import logging

from botbuilder.core import BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

from app.channels.teams_bot import MeridianTeamsBot
from app.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Adapter + bot — created once at module import time.
# ---------------------------------------------------------------------------

_settings = get_settings()

_adapter_settings = BotFrameworkAdapterSettings(
    app_id=_settings.teams_app_id,
    app_password=_settings.teams_app_password,
)
_adapter = BotFrameworkAdapter(_adapter_settings)
_bot = MeridianTeamsBot()


async def _on_adapter_error(context, error: Exception) -> None:  # type: ignore[type-arg]
    """Log adapter-level errors and send the user a friendly message."""
    logger.exception("Bot adapter error: %s", error)
    try:
        await context.send_activity("❌ An internal error occurred. Please try again.")
    except Exception:
        pass  # ignore send errors during error handling


_adapter.on_turn_error = _on_adapter_error  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter()


@router.post("/api/messages")
async def messages(request: Request) -> Response:
    """Receive Bot Framework activities from Azure Bot Service / Teams."""
    logger.info(
        "POST /api/messages received  content-type=%s  from=%s",
        request.headers.get("Content-Type", "<none>"),
        request.client,
    )
    if "application/json" not in request.headers.get("Content-Type", ""):
        return Response(status_code=415)

    body = await request.json()
    activity = Activity().deserialize(body)
    # msrest camelCase→snake_case deserialization silently drops serviceUrl in
    # some edge cases; patch it explicitly from the raw dict so the adapter can
    # always POST replies back to the channel / emulator service URL.
    if not activity.service_url:
        activity.service_url = body.get("serviceUrl") or ""
    logger.debug(
        "activity type=%s service_url=%s channel_id=%s",
        activity.type,
        activity.service_url,
        activity.channel_id,
    )
    auth_header = request.headers.get("Authorization", "")

    try:
        invoke_response = await _adapter.process_activity(
            activity, auth_header, _bot.on_turn
        )
    except PermissionError as exc:
        logger.warning("Bot Framework auth rejected: %s", exc)
        return Response(status_code=401)
    except Exception as exc:
        logger.exception("Unhandled error processing Teams activity: %s", exc)
        return Response(status_code=500)

    if invoke_response:
        return JSONResponse(
            content=invoke_response.body,
            status_code=invoke_response.status,
        )
    return Response(status_code=200)
