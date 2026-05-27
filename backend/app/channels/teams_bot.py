"""Teams / M365 Copilot bot handler for FabricMA.

Architecture
------------
MeridianTeamsBot extends botbuilder's ActivityHandler.  It is wired into a
BotFrameworkAdapter in app/api/teams.py which:
  1. Validates the Bot Framework JWT on every POST /api/messages request.
  2. Calls bot.on_turn(turn_context) to dispatch to the right handler below.

Streaming
---------
Teams + M365 Copilot support progressive text delivery via the channel_data
"streamType" protocol introduced for Custom Engine Agents:

  • An initial activity (type=typing, streamType="streaming", streamSequence=1)
    creates the streaming slot in the UI and returns a streamId.
  • Incremental updates (type=typing, same id, streamType="streaming",
    growing streamSequence) replace the placeholder text progressively.
  • A final activity (type=message, same id, streamType="final") commits the
    complete text as a permanent message.

Regular Teams bot channels that do not support the protocol will show a normal
typing indicator and fall back to the final message gracefully.

HITL
----
When the orchestrator returns a "hitl" event an Adaptive Card with Approve /
Reject buttons is sent.  On Approve, dispatch_with_plan() re-executes the
previously-chosen routing plan directly, skipping the orchestrator re-routing
step that would otherwise trigger hitl again.

SSO / OBO
---------
If Teams SSO is configured in the app manifest (webApplicationInfo section),
the signed-in user's access token arrives in activity.channel_data["ssoToken"].
That token is passed as user_assertion to OnBehalfOfCredential so Foundry calls
run under the user's identity.  When SSO is not configured (e.g. during local
development or early testing) the bot falls back to its own client-secret
credential — Foundry calls succeed but run under the bot's app identity.
"""

from __future__ import annotations

import asyncio
import logging
from typing import List

from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity, ActivityTypes, Attachment, ChannelAccount

from app.channels.cards import build_hitl_card, build_plan_card
from app.config import get_settings
from app.services.orchestrator import OrchestratorService
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

_settings = get_settings()
_session_service = SessionService()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_sso_token(turn_context: TurnContext) -> str | None:
    """Return the Teams SSO access token from the activity, or None."""
    cd = getattr(turn_context.activity, "channel_data", None)
    if isinstance(cd, dict):
        return cd.get("ssoToken") or None
    return None


def _make_streaming_activity(
    *,
    stream_id: str | None,
    text: str,
    seq: int,
    final: bool = False,
) -> Activity:
    """Build a channel_data streaming activity for M365 Copilot CE agent protocol.

    When final=False the type is "typing" so regular Teams channels treat it as
    a standard typing indicator.  When final=True the type is "message" so the
    text is committed as a permanent message regardless of the channel.
    """
    channel_data: dict = {"streamSequence": seq}
    if final:
        channel_data["streamType"] = "final"
        if stream_id:
            channel_data["streamId"] = stream_id
        return Activity(
            type=ActivityTypes.message,
            id=stream_id,
            text=text,
            channel_data=channel_data,
        )
    else:
        channel_data["streamType"] = "streaming"
        if stream_id:
            channel_data["streamId"] = stream_id
        return Activity(
            type=ActivityTypes.typing,
            id=stream_id,
            text=text,
            channel_data=channel_data,
        )


def _adaptive_card_activity(card: dict) -> Activity:
    return Activity(
        type=ActivityTypes.message,
        attachments=[
            Attachment(
                content_type="application/vnd.microsoft.card.adaptive",
                content=card,
            )
        ],
    )


async def _safe_send(turn_context: TurnContext, activity_or_text) -> None:
    """Send an activity, logging and swallowing send-level errors.

    Used inside the streaming event loop so that a single failed send
    (e.g. transient network blip, or the initial service_url issue during
    local emulator startup) doesn't abort the entire response delivery.
    """
    try:
        await turn_context.send_activity(activity_or_text)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("send_activity failed (swallowed): %s", exc)


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------

class MeridianTeamsBot(ActivityHandler):
    """Main bot handler for the Meridian Supply Co. multi-agent analytics."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ) -> None:
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await _safe_send(
                    turn_context,
                    "👋 Welcome to **Meridian Supply Co. Analytics**!\n\n"
                    "Ask me anything about invoices, inventory, or sales — for example:\n"
                    "- *What are the top 5 customers by revenue this quarter?*\n"
                    "- *Which warehouses are below reorder threshold?*\n"
                    "- *Compare territory sales performance year-over-year.*",
                )

    # ------------------------------------------------------------------
    # Message handling
    # ------------------------------------------------------------------

    async def on_message_activity(self, turn_context: TurnContext) -> None:
        # Adaptive Card submit (HITL approve / reject)
        if turn_context.activity.value:
            await self._handle_card_action(turn_context)
            return

        query = (turn_context.activity.text or "").strip()
        if not query:
            return

        # Fire-and-forget: do NOT await here.  process_activity must return
        # quickly (200 OK) so the channel/emulator doesn't time out waiting for
        # the response.  _stream_dispatch then pushes activities back to the
        # channel via turn_context.send_activity using the serviceUrl.
        asyncio.ensure_future(
            self._stream_dispatch(turn_context, query, approved_plan=None)
        )

    # ------------------------------------------------------------------
    # Core streaming dispatch
    # ------------------------------------------------------------------

    async def _stream_dispatch(
        self,
        turn_context: TurnContext,
        query: str,
        *,
        approved_plan: dict | None,
    ) -> None:
        """Drive the orchestrator and stream results back to the channel.

        When approved_plan is set (post-HITL approval), dispatch_with_plan() is
        used to execute the plan directly without re-routing through the LLM.
        """
        session = _session_service.create_session()
        user_token = _extract_sso_token(turn_context)
        orchestrator = OrchestratorService(_settings, user_token=user_token)

        # Open the streaming slot: send initial typing activity and capture the
        # streamId that the channel assigns.  Falls back gracefully if the channel
        # does not return an id (e.g. the Bot Framework Emulator).
        init_activity = _make_streaming_activity(
            stream_id=None, text="", seq=1, final=False
        )
        stream_id: str | None = None
        try:
            init_response = await turn_context.send_activity(init_activity)
            stream_id = getattr(init_response, "id", None) or None
        except Exception as exc:
            logger.debug("Streaming slot open failed (non-fatal): %s", exc)
            stream_id = None

        accumulated = ""
        seq = 1

        event_source = (
            orchestrator.dispatch_with_plan(query, session.session_id, approved_plan)
            if approved_plan is not None
            else orchestrator.dispatch(query, session.session_id)
        )

        try:
            async for event in event_source:
                etype = event["type"]

                if etype == "plan":
                    await _safe_send(
                        turn_context,
                        _adaptive_card_activity(build_plan_card(event["data"])),
                    )

                elif etype == "status":
                    msg = event["data"].get("message", "")
                    if msg:
                        seq += 1
                        await _safe_send(
                            turn_context,
                            _make_streaming_activity(
                                stream_id=stream_id,
                                text=f"_{msg}_",
                                seq=seq,
                                final=False,
                            ),
                        )

                elif etype == "token":
                    chunk = event["data"].get("text", "")
                    accumulated += chunk
                    seq += 1
                    await _safe_send(
                        turn_context,
                        _make_streaming_activity(
                            stream_id=stream_id,
                            text=accumulated,
                            seq=seq,
                            final=False,
                        ),
                    )

                elif etype == "hitl":
                    # Finalise any partial stream before showing the approval card
                    if accumulated:
                        seq += 1
                        await _safe_send(
                            turn_context,
                            _make_streaming_activity(
                                stream_id=stream_id,
                                text=accumulated,
                                seq=seq,
                                final=True,
                            ),
                        )
                    hitl_plan = event["data"].get("plan", {})
                    _session_service.store_hitl_pending(
                        session.session_id,
                        {"query": query, "plan": hitl_plan},
                    )
                    await _safe_send(
                        turn_context,
                        _adaptive_card_activity(
                            build_hitl_card(session.session_id, hitl_plan, query)
                        ),
                    )
                    return

                elif etype == "done":
                    pass  # handled below

            # Commit the final streamed text as a permanent message
            if accumulated:
                seq += 1
                await _safe_send(
                    turn_context,
                    _make_streaming_activity(
                        stream_id=stream_id,
                        text=accumulated,
                        seq=seq,
                        final=True,
                    ),
                )
            else:
                # Orchestrator returned nothing — close the stream gracefully
                await _safe_send(
                    turn_context,
                    _make_streaming_activity(
                        stream_id=stream_id,
                        text="No response generated.",
                        seq=seq + 1,
                        final=True,
                    ),
                )

        except Exception as exc:
            logger.exception("Teams dispatch error: %s", exc)
            await _safe_send(turn_context, f"❌ An error occurred: {exc!s}")

    # ------------------------------------------------------------------
    # Adaptive Card action handler
    # ------------------------------------------------------------------

    async def _handle_card_action(self, turn_context: TurnContext) -> None:
        value: dict = turn_context.activity.value or {}
        action = value.get("action")

        if action == "hitl_approve":
            session_id: str = value.get("session_id", "")
            original_query: str = value.get("original_query", "")

            # Retrieve the stored plan before resolving so we can use it for
            # dispatch_with_plan() and avoid re-triggering the hitl branch.
            stored_session = _session_service.get_session(session_id)
            saved_plan = (
                stored_session.hitl_pending.get("plan")
                if stored_session and stored_session.hitl_pending
                else None
            )
            _session_service.resolve_hitl(session_id, approved=True)

            await _safe_send(turn_context, "✅ Approved — processing your request…")
            await self._stream_dispatch(
                turn_context,
                original_query,
                approved_plan=saved_plan,
            )

        elif action == "hitl_reject":
            session_id = value.get("session_id", "")
            _session_service.resolve_hitl(session_id, approved=False)
            await _safe_send(
                turn_context,
                "❌ Request rejected. Feel free to ask a different question.",
            )

        else:
            logger.warning("Unrecognised card action received: %s", action)
