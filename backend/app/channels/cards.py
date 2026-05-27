"""Adaptive Card builders for the Teams / M365 Copilot channel.

All functions return plain dicts that serialise to Adaptive Card JSON (schema v1.5).
They are attached to Bot Framework Activity objects as:

    Attachment(
        content_type="application/vnd.microsoft.card.adaptive",
        content=build_plan_card(plan),
    )
"""

from __future__ import annotations


def build_plan_card(plan: dict) -> dict:
    """Routing-plan card shown before agents run.

    Displays the pattern, rationale, and which domain agents will be called.
    """
    pattern: str = plan.get("pattern", "single").upper()
    rationale: str = plan.get("rationale", "")
    agents: list[str] = plan.get("agents", [])
    steps: list[str] = plan.get("steps", [])

    pattern_icon = {
        "SINGLE": "🎯",
        "CONCURRENT": "⚡",
        "SEQUENTIAL": "🔗",
        "HITL": "🙋",
    }.get(pattern, "🤖")

    agent_items = [
        {
            "type": "TextBlock",
            "text": f"• {a.title()} Agent",
            "spacing": "None",
            "size": "Small",
            "color": "Accent",
        }
        for a in agents
    ]

    step_items = [
        {
            "type": "TextBlock",
            "text": f"{i + 1}. {s}",
            "wrap": True,
            "spacing": "None",
            "size": "Small",
            "isSubtle": True,
        }
        for i, s in enumerate(steps)
    ]

    body = [
        {
            "type": "Container",
            "style": "accent",
            "bleed": True,
            "items": [
                {
                    "type": "TextBlock",
                    "text": f"{pattern_icon} Routing Plan — {pattern}",
                    "weight": "Bolder",
                    "size": "Medium",
                    "color": "Light",
                },
                {
                    "type": "TextBlock",
                    "text": rationale,
                    "wrap": True,
                    "size": "Small",
                    "color": "Light",
                    "spacing": "Small",
                },
            ],
        },
    ]

    if agent_items:
        body += [
            {
                "type": "TextBlock",
                "text": "Agents",
                "weight": "Bolder",
                "spacing": "Medium",
                "size": "Small",
            },
            *agent_items,
        ]

    if step_items:
        body += [
            {
                "type": "TextBlock",
                "text": "Steps",
                "weight": "Bolder",
                "spacing": "Medium",
                "size": "Small",
            },
            *step_items,
        ]

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": body,
    }


def build_hitl_card(session_id: str, plan: dict, original_query: str) -> dict:
    """Human-in-the-loop approval card with Approve / Reject buttons.

    On submit, the card sends an Action.Submit payload:
        { "action": "hitl_approve" | "hitl_reject",
          "session_id": "<id>",
          "original_query": "<query>" }
    """
    agents: list[str] = plan.get("agents", [])
    agent_list = ", ".join(f"**{a.title()}**" for a in agents) or "unknown agents"
    rationale: str = plan.get("rationale", "")

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {
                "type": "Container",
                "style": "warning",
                "bleed": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": "⚠️ Human Approval Required",
                        "weight": "Bolder",
                        "size": "Medium",
                    },
                ],
            },
            {
                "type": "TextBlock",
                "text": f"The orchestrator wants to call {agent_list}.",
                "wrap": True,
                "spacing": "Medium",
            },
            {
                "type": "TextBlock",
                "text": rationale,
                "wrap": True,
                "isSubtle": True,
                "size": "Small",
            },
            {
                "type": "TextBlock",
                "text": f"**Query:** _{original_query}_",
                "wrap": True,
                "spacing": "Small",
                "size": "Small",
            },
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "✅ Approve",
                "style": "positive",
                "data": {
                    "action": "hitl_approve",
                    "session_id": session_id,
                    "original_query": original_query,
                },
            },
            {
                "type": "Action.Submit",
                "title": "❌ Reject",
                "style": "destructive",
                "data": {
                    "action": "hitl_reject",
                    "session_id": session_id,
                },
            },
        ],
    }
