# FabricMA — Multi-Agent Analytics Platform

Meridian Supply Co.'s intelligent analytics platform built on Microsoft Agent Framework, Azure AI Foundry Agents (Responses API v2), and Microsoft Fabric Data Agents.

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │         React Frontend               │
                    │   MSAL Auth │ Zustand │ SSE Stream   │
                    └──────────────┬──────────────────────┘
                                   │ HTTPS + Bearer token
                    ┌──────────────▼──────────────────────┐
                    │      FastAPI Backend (Python)         │
                    │  OBO Flow │ SSE │ Session Store       │
                    └──────────────┬──────────────────────┘
                                   │ OnBehalfOfCredential
                    ┌──────────────▼──────────────────────┐
                    │    Azure AI Foundry Agents           │
                    │  Orchestrator (o4-mini thinking)     │
                    │  ├─ Invoice Agent (gpt-4.1-mini)     │
                    │  ├─ Inventory Agent (gpt-4.1-mini)   │
                    │  └─ Sales Agent (gpt-4.1-mini)       │
                    └──────────────┬──────────────────────┘
                                   │ MicrosoftFabricPreviewTool
                    ┌──────────────▼──────────────────────┐
                    │      Microsoft Fabric Data Agents    │
                    │  MeridianSupplyCo Lakehouse          │
                    │  (Invoice │ Inventory │ Sales)       │
                    └─────────────────────────────────────┘
```

## Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- Node.js 20+ and npm
- Azure subscription with:
  - Azure AI Foundry project (with o4-mini and gpt-4.1-mini deployed)
  - Microsoft Entra app registration (backend + SPA)
  - Microsoft Fabric workspace with `MeridianSupplyCo` lakehouse

## Quickstart

### 1. Clone and configure

```bash
git clone <repo-url>
cd fabricma
cp .env.example .env
# Edit .env with your Azure credentials
```

### 2. Provision Fabric data layer

1. Upload CSV files from `fabric/seed_data/` to your Fabric Lakehouse `Files/seed_data/`
2. Run notebooks `nb_00` through `nb_12` in Fabric in order
3. Create three Fabric Data Agents (Invoice, Inventory, Sales) pointing to the lakehouse
4. Create three Foundry project connections (one per Fabric Data Agent)
5. Update `.env` with `FABRIC_CONNECTION_*` values

### 3. Provision Foundry agents

```bash
cd backend
uv sync
uv run python ../scripts/provision_agents.py
```

### 4. Run locally

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
cp .env.example .env  # fill in VITE_* values
npm install
npm run dev
```

Visit http://localhost:5173 and sign in with your Microsoft account.

### 5. Docker Compose (optional)

```bash
docker compose up --build
```

## Orchestration Patterns

| Pattern | Description | Example |
|---|---|---|
| **Single** | Routes to one domain agent | "What is the current DSO?" |
| **Concurrent** | Runs multiple agents in parallel | "Show me invoices AND inventory for product X" |
| **Sequential** | Chains agents, passing context forward | "Which overdue customers also have low order frequency?" |
| **HITL** | Pauses for human approval before proceeding | "Should we place a supplier reorder?" |

## Teams / M365 Copilot Publishing

Publishing the Orchestrator agent to Microsoft Teams and M365 Copilot requires Early Access Preview access.

### Steps

1. **Register Azure Bot Service provider**: In Azure portal, register the `Microsoft.BotService` resource provider on your subscription.
2. **Publish in Foundry portal**: Navigate to your Azure AI Foundry project → Agents → `meridian-orchestrator-agent` → **Publish** tab → Select "Microsoft Teams" and/or "Microsoft 365 Copilot".
3. **Admin center approval**: In [Microsoft 365 Admin Center](https://admin.microsoft.com), go to Teams apps → Manage apps → find the agent and **Approve** it.
4. **Re-apply RBAC**: After publishing, re-apply `agentIdentityId` RBAC on the Foundry project so the agent can call Fabric Data Agents using OBO credentials.
5. **Test in Teams**: The agent appears as a bot in Teams; users can @mention it or chat directly.

> **Note**: Teams/M365 publish is in Early Access Preview as of May 2026. Check [Azure AI Foundry documentation](https://learn.microsoft.com/azure/foundry/agents/how-to/publish-copilot) for GA status.

## Environment Variables

See `.env.example` for the complete variable reference. Key variables:

| Variable | Description |
|---|---|
| `AZURE_TENANT_ID` | Entra tenant ID |
| `AZURE_CLIENT_ID` | Backend app registration client ID |
| `AZURE_CLIENT_SECRET` | Backend app registration client secret |
| `AZURE_AI_PROJECT_ENDPOINT` | Foundry project endpoint URL |
| `FABRIC_CONNECTION_*` | Friendly names of Foundry connections to Fabric Data Agents |
