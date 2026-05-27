---
title: "FabricMA — Microsoft Teams Deployment Guide"
description: "Step-by-step instructions for running the FabricMA Teams bot locally with the Bot Framework Emulator and deploying it to production Microsoft Teams / M365 Copilot."
---

## Overview

FabricMA ships a **Custom Engine Agent** for Microsoft Teams and M365 Copilot. The bot is implemented as a `BotFrameworkAdapter`-based `ActivityHandler` (`MeridianTeamsBot`) grafted onto the existing FastAPI backend. It reuses the same `OrchestratorService`, Foundry agents, and Fabric data connections as the React SPA — the only difference is the channel (Teams vs browser).

### What the Teams integration delivers

- Natural-language supply-chain analytics in any Teams chat or M365 Copilot panel
- **Progressive streaming** — answers build word-by-word using the M365 CE Agent `streamType` protocol
- **Adaptive Cards** for routing plan previews (which agents were invoked, and why)
- **Human-in-the-Loop (HITL)** approval cards — when the orchestrator needs confirmation before executing a multi-agent plan, the user gets an Approve / Reject card instead of a blind execution
- **Teams SSO** — the signed-in user's identity flows through to Foundry via OBO, so all Fabric queries run under the user's own permissions (same as the SPA)

---

## Architecture

```
Teams client / M365 Copilot
        │  HTTPS activity (Bot Framework protocol)
        ▼
Azure Bot Service  ──────────────────────────────────────────────────────────┐
        │  POST /api/messages  (JWT-validated by BotFrameworkAdapter)        │
        ▼                                                                    │
FastAPI backend  (app/api/teams.py + app/channels/teams_bot.py)             │
        │                                                                    │
        ├─ BotFrameworkAdapter.process_activity()                           │
        │       └─ MeridianTeamsBot.on_turn()                               │
        │               ├─ on_members_added → welcome card                  │
        │               ├─ on_message_activity → asyncio background task    │
        │               │       └─ _stream_dispatch()                       │
        │               │               ├─ OrchestratorService (OBO cred)  │
        │               │               ├─ stream routing plan card         │
        │               │               ├─ stream token-by-token typing     │
        │               │               └─ commit final message             │
        │               └─ _handle_card_action → HITL approve / reject      │
        │                                                                    │
        └─ Returns HTTP 200 immediately (fire-and-forget dispatch)          │
                                                                             │
                                                ◄────── reply activities ───┘
                                              (via serviceUrl / Bot Service)
```

### Credential flow

| Scenario | Credential used | Why |
|---|---|---|
| Normal Teams message (SSO configured) | `OnBehalfOfCredential` with the user's `ssoToken` | Foundry + Fabric queries run as the signed-in user |
| Teams message (SSO not yet configured) | `ClientSecretCredential` (bot service principal) | Bot's own identity; requires Azure AI Developer role on Foundry |
| Local emulator / dev (`TEAMS_APP_ID` empty) | `AzureCliCredential` | Developer's `az login` identity; has full Fabric access |

---

## Part 1 — Local Development with Bot Framework Emulator

### Prerequisites

- Python 3.11+, `uv` package manager
- [Bot Framework Emulator v4](https://github.com/microsoft/BotFramework-Emulator/releases) installed
- Azure CLI logged in (`az login`) with an account that has access to the Foundry project and Fabric workspace
- `.env` file configured at the repo root (see existing `.env.example`)

### 1.1 — Ensure Teams keys are absent from `.env`

When `TEAMS_APP_ID` is empty, the backend runs in **unauthenticated emulator mode** and uses your `az login` identity for all Foundry calls. Do not set these for local development:

```dotenv
# Leave blank for emulator mode
TEAMS_APP_ID=
TEAMS_APP_PASSWORD=
```

### 1.2 — Start the backend with dual-stack binding

The Bot Framework Emulator (a Node.js/Electron app) resolves `localhost` to `::1` (IPv6) on Windows. The backend must bind to both IPv4 and IPv6:

```bat
# run-backend.bat already uses --host :: which enables dual-stack on Windows
run-backend.bat
```

Verify startup — you should see:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://[::]:8000
```

### 1.3 — Connect the emulator

1. Open Bot Framework Emulator
2. Click **Open Bot** (Welcome tab)
3. Enter the bot URL: `http://localhost:8000/api/messages`
4. Leave **Microsoft App ID** and **Microsoft App Password** blank
5. Click **Connect**

You should see:
```
[timestamp] Connecting to bot on http://localhost:8000/api/messages
[timestamp] Emulator listening on http://[::]:50958
[timestamp] -> conversationUpdate
[timestamp] POST 200 directline/conversations/<id>/activities
[timestamp] <- message 👋 Welcome to Meridian Supply Co. Analytics!
```

### 1.4 — Test a query

Type a question such as:
> How many invoices are still unpaid from 2024, and what is their combined value?

Expected sequence in the emulator:
1. 🟦 **Routing Plan card** — shows which agent(s) will be called and the routing rationale
2. ⌨️ Typing indicator with status messages ("Routing query...", "Calling invoice agent...")
3. 📝 Final answer streaming in progressively
4. ✅ Complete answer committed as a permanent message

### 1.5 — Troubleshooting emulator issues

| Symptom | Cause | Fix |
|---|---|---|
| `POST 404` in emulator log | Wrong URL (missing `s`) | Use `/api/messages` not `/api/message` |
| `POST 400` in emulator log | Emulator can't reach backend (IPv6 vs IPv4) | Ensure `--host ::` in uvicorn start command; use `http://localhost:8000/api/messages` not `127.0.0.1` |
| `Create assistant failed: tool_user_error` | Service principal can't access Fabric tool connections | Ensure `TEAMS_APP_ID` is empty so `AzureCliCredential` is used; run `az login` |
| "Send failed. Retry." in emulator UI | Backend returned non-200 | Check backend terminal for stack trace |
| No welcome message | `on_members_added_activity` error | Check backend logs; ensure Entra app registration has `access_as_user` scope |

---

## Part 2 — Production Deployment to Microsoft Teams

### 2.1 — Azure Bot Service registration

1. In the Azure portal, create an **Azure Bot** resource:
   - **Bot handle**: choose a unique name (e.g. `meridian-fabricma-bot`)
   - **Type**: Multi-Tenant
   - **Microsoft App ID**: use **existing** — enter the `AZURE_CLIENT_ID` from your `.env` (or create a new app registration and use its client ID)
   - **Resource group**: same as your Foundry project

2. Under **Configuration**, set:
   - **Messaging endpoint**: `https://<your-backend-domain>/api/messages`
   - Save

3. Under **Channels**, enable:
   - **Microsoft Teams** (for Teams integration)
   - **M365 Extensions** (for M365 Copilot integration, if licensed)

4. Note the **Microsoft App ID** and generate a **client secret** under the app registration in Entra ID.

### 2.2 — Update `.env` / deployment environment variables

```dotenv
TEAMS_APP_ID=<Microsoft App ID from step 2.1>
TEAMS_APP_PASSWORD=<client secret from step 2.1>
```

These two values switch the backend from emulator mode (AzureCliCredential) to production mode (JWT validation + ClientSecretCredential fallback).

### 2.3 — Configure Teams SSO (strongly recommended)

SSO allows the signed-in Teams user's identity to flow through to Foundry via OBO, giving each user their own Fabric data access permissions.

#### In the Entra app registration (Azure portal → Entra ID → App registrations → `<TEAMS_APP_ID>`)

1. **Expose an API**:
   - Set the Application ID URI to `api://<bot-domain>/<TEAMS_APP_ID>`
     (e.g. `api://meridian.contoso.com/fb3c0e70-...`)
   - Add a scope named `access_as_user`:
     - Who can consent: **Admins and users**
     - Display name: `Access FabricMA as the signed-in user`
2. **Authorized client applications** — add the Teams clients:
   - `1fec8e78-bce4-4aaf-ab1b-5451cc387264` (Teams desktop/mobile)
   - `5e3ce6c0-2b1f-4285-8d4b-75ee78787346` (Teams web)

#### In your Teams app manifest

Add the `webApplicationInfo` section:

```json
{
  "webApplicationInfo": {
    "id": "<TEAMS_APP_ID>",
    "resource": "api://<bot-domain>/<TEAMS_APP_ID>"
  }
}
```

Once SSO is active, every user message from Teams carries a `ssoToken` in `channel_data`. The backend reads it in `_extract_sso_token()` and passes it to `OrchestratorService` as `user_token`, triggering OBO — all Foundry and Fabric calls run under the user's own identity.

### 2.4 — Deploy the backend

The backend ships as a Docker image. Any Azure container host works:

```bash
# Build and push
docker build -t <registry>.azurecr.io/fabricma-backend:latest ./backend
docker push <registry>.azurecr.io/fabricma-backend:latest
```

Recommended hosting options (in order of simplicity):
1. **Azure Container Apps** — serverless, auto-scales to zero, handles HTTPS automatically
2. **Azure App Service (Linux)** — PaaS, simpler networking
3. **Azure Kubernetes Service** — full control, needed for high-availability

Ensure the hosting environment has all `.env` variables set as **application settings / environment variables**, including `TEAMS_APP_ID` and `TEAMS_APP_PASSWORD`.

### 2.5 — Package and sideload the Teams app

1. Create a Teams app manifest (`manifest.json`) with:
   - `"id"`: a new GUID for the Teams app package
   - `"bots"`: entry pointing to your `TEAMS_APP_ID`
   - `"webApplicationInfo"`: as configured in 2.3
   - Appropriate permissions scopes

2. Zip `manifest.json` + two icon files (outline + color, 32×32 and 192×192 PNG)

3. Sideload for testing:
   - Teams → Apps → Manage your apps → Upload a custom app

4. For org-wide deployment:
   - Submit through Teams Admin Center → Manage apps → Upload

### 2.6 — Role assignments required on Azure resources

The bot service principal (`TEAMS_APP_ID`) needs:

| Resource | Role | Purpose |
|---|---|---|
| Azure AI Services account (`astaieus2`) | **Azure AI Developer** | Call Foundry agents API |
| Fabric workspace | **Viewer** or **Contributor** | Access lakehouse data (only needed if not using OBO) |

With SSO + OBO configured (section 2.3), the user's own Entra permissions govern Fabric access and the service principal only needs the Foundry role.

```bash
az role assignment create \
  --assignee "<TEAMS_APP_ID>" \
  --role "Azure AI Developer" \
  --scope "/subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.CognitiveServices/accounts/<FOUNDRY_ACCOUNT>"
```

---

## Part 3 — How Streaming Works in Teams

The M365 Custom Engine Agent protocol delivers progressive answers without requiring the user to wait for the full response.

### Protocol sequence

```
Bot → Teams:  Activity { type=typing, channelData.streamType="streaming", streamSequence=1, text="" }
              ↳ Teams creates a placeholder message slot, returns streamId

Bot → Teams:  Activity { type=typing, id=<streamId>, streamType="streaming", streamSequence=2, text="There are 2,017..." }
              ↳ Teams updates the placeholder in place

Bot → Teams:  Activity { type=typing, id=<streamId>, streamType="streaming", streamSequence=3, text="There are 2,017 unpaid..." }
              ↳ Teams updates again (text grows)

Bot → Teams:  Activity { type=message, id=<streamId>, channelData.streamType="final", text="<complete answer>" }
              ↳ Teams commits as a permanent message
```

In the Bot Framework Emulator (which does not support the `streamType` protocol), the typing indicators appear as individual messages and the final message is committed normally — functionally correct, just without the progressive animation.

---

## Part 4 — Human-in-the-Loop (HITL) in Teams

When the orchestrator determines a query requires cross-domain agents (e.g. invoices + inventory), it can pause and ask for approval before executing.

### Flow

1. Orchestrator emits a `hitl` event with the proposed routing plan
2. Bot sends an **Adaptive Card** with the plan details and **Approve** / **Reject** buttons
3. User taps Approve → bot receives a card submit activity, retrieves the stored plan, and calls `dispatch_with_plan()` to execute it directly (bypassing re-routing)
4. User taps Reject → bot sends a cancellation message

The plan is stored in `SessionService` under `hitl_pending` keyed by `session_id`, so the approval can arrive in a separate HTTP request from the original query.

---

## Environment Variable Reference

| Variable | Required for Teams | Description |
|---|---|---|
| `TEAMS_APP_ID` | Production only | Microsoft App ID of the Azure Bot registration. Leave empty for emulator dev. |
| `TEAMS_APP_PASSWORD` | Production only | Client secret for the bot app registration. |
| `AZURE_CLIENT_ID` | Always | Service principal used for Foundry calls when no user OBO token is available. |
| `AZURE_CLIENT_SECRET` | Always | Secret for the service principal. |
| `AZURE_TENANT_ID` | Always | Entra tenant ID. |
| `AZURE_AI_PROJECT_ENDPOINT` | Always | Azure AI Foundry project endpoint URL. |
| `AZURE_AUDIENCE` | Always | Audience for JWT validation of SPA tokens (`api://<client-id>`). |
