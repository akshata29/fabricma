---
title: "FabricMA — Architecture and Design Reference"
description: "End-to-end architecture, Azure services, Microsoft Agent Framework patterns, design decisions, and best practices for the FabricMA multi-agent analytics platform."
---

## Overview

FabricMA is Meridian Supply Co.'s intelligent analytics platform. It combines a React single-page application, a Python FastAPI backend, Azure AI Foundry Agents (Responses API v2), and Microsoft Fabric Data Agents to deliver natural-language supply-chain analytics over a lakehouse. Users type a question in plain English; an orchestrator agent decides which domain specialist agents to invoke, those agents query Fabric via SQL, and a streamed answer is returned to the browser in real time.

---

## System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Browser (React SPA)                        │
│  MSAL Auth  │  Zustand State  │  SSE Stream Reader            │
│  TailwindCSS + shadcn/ui + Radix primitives                   │
└───────────────────────────┬──────────────────────────────────┘
                            │  HTTPS  Bearer token
┌───────────────────────────▼──────────────────────────────────┐
│              FastAPI Backend  (Python 3.11+)                  │
│  CorrelationID MW │ RequestLogging MW │ CORS │ GZip           │
│  JWT Validation (PyJWT + JWKS)                                │
│  OrchestratorService  │  SessionService  │  AgentService      │
└───────────────────────────┬──────────────────────────────────┘
                            │  OnBehalfOfCredential (OBO)
┌───────────────────────────▼──────────────────────────────────┐
│              Azure AI Foundry Agents                          │
│  Orchestrator Agent  (gpt-4.1-mini)                          │
│    ├─ Invoice Agent   (gpt-4.1-mini)                          │
│    ├─ Inventory Agent (gpt-4.1-mini)                          │
│    └─ Sales Agent     (gpt-4.1-mini)                          │
└───────────────────────────┬──────────────────────────────────┘
                            │  MicrosoftFabricPreviewTool
┌───────────────────────────▼──────────────────────────────────┐
│              Microsoft Fabric Data Agents                     │
│  MeridianSupplyCo Lakehouse                                   │
│  Invoice lakehouse │ Inventory lakehouse │ Sales lakehouse    │
└──────────────────────────────────────────────────────────────┘
```

---

## Azure Services Used

| Service | Role |
|---|---|
| **Azure AI Foundry** | Hosts all four agents (Orchestrator, Invoice, Inventory, Sales) using the Responses API v2 (`azure-ai-projects` SDK). Provides versioned `PromptAgentDefinition` management. |
| **Azure AI models** | `gpt-4.1-mini` powers all domain agents. The orchestrator config also references `o4-mini` as the extended-thinking model for complex routing decisions. |
| **Microsoft Fabric Data Agents** | Three dedicated Fabric Data Agents expose the `MeridianSupplyCo` lakehouse tables over natural-language SQL via the `MicrosoftFabricPreviewTool`. Each is connected to the Foundry project through a `ToolProjectConnection`. |
| **Microsoft Fabric Lakehouse** | Star-schema lakehouse with dimension and fact tables seeded from CSV files and built by PySpark notebooks (`nb_00`–`nb_12`). Tables: `FactInvoice`, `FactInvoiceLine`, `FactSales`, `FactInventorySnapshot`, `FactStockMovement`, plus shared dimension tables. |
| **Microsoft Entra ID** | Provides user authentication (OAuth 2.0 Authorization Code + PKCE for the SPA) and backend app-identity. Used for On-Behalf-Of (OBO) token exchange so the backend calls Foundry under the signed-in user's identity. |
| **Azure Container Registry / Docker** | Both services ship as Docker images defined by their respective `Dockerfile` files. `docker compose` orchestrates them locally; the same images are deployable to any Azure container host. |

---

## Frontend Architecture

### Technology Stack

| Concern | Choice | Rationale |
|---|---|---|
| Framework | React 18 | Component model, concurrent rendering |
| Language | TypeScript 5 | Type safety across store, hooks, API layer |
| Build tool | Vite 5 | Fast HMR, ESM-native, optimized production bundles |
| Styling | Tailwind CSS 3 + shadcn/ui + Radix UI primitives | Utility-first CSS, accessible unstyled components |
| State management | Zustand 4 | Minimal boilerplate, fine-grained subscriptions |
| Auth | `@azure/msal-browser` v4 + `@azure/msal-react` v3 | Standard MSAL for SPA OAuth 2.0 + PKCE flows |
| HTTP | Axios (REST calls) + native `fetch` (SSE stream) | Axios interceptors for Bearer injection; `fetch` for ReadableStream |

### Component Tree

```
App
 ├─ AuthenticatedTemplate
 │   └─ AppShell
 │       ├─ Sidebar            — session history, agent selector
 │       └─ ChatPanel          — input bar, message list, status
 │           ├─ PlanPreview    — displays the orchestrator JSON plan
 │           └─ ApprovalDialog — HITL modal overlay
 └─ UnauthenticatedTemplate
     └─ SignInPage             — MSAL loginPopup trigger
```

### State Management with Zustand

Four independent stores are kept lean and purpose-scoped:

| Store | Responsibility |
|---|---|
| `chatStore` | Active message list, streaming flag, status message, pending HITL data, current orchestrator plan |
| `sessionStore` | Current active session ID |
| `historyStore` | Persisted list of past sessions with their message arrays; used by the sidebar |
| `agentStore` | Available agents fetched from the API and any optional user agent selection |

### Authentication Flow

1. On app load, MSAL checks for a cached token silently (`acquireTokenSilent`).
2. If none exists, `loginPopup` opens the Entra login dialog.
3. After sign-in, `useAuthToken.getToken()` acquires a scoped access token for the backend API scope (`VITE_AZURE_BACKEND_SCOPE`).
4. A token-provider function is registered on the Axios `apiClient` interceptor at app start (inside `AppShell`), injecting `Authorization: Bearer <token>` on every request.

### Server-Sent Events (SSE) Stream

The chat interaction uses a manual `fetch + ReadableStream` pipeline rather than `EventSource`, giving full control over request headers (required for the `Authorization` header, which `EventSource` does not support).

The `useChatStream` hook:

1. POSTs `{ query, session_id }` to `/api/v1/chat/stream`.
2. Reads the response body as a `ReadableStream`, decoding chunked SSE frames.
3. Dispatches typed events to Zustand stores:

| SSE event | Zustand action |
|---|---|
| `plan` | `setCurrentPlan` — stores the orchestrator routing plan |
| `status` | `setStatusMessage` — shows progress text (e.g. "Running invoice agent…") |
| `token` | `appendToken` — appends streamed text to the last assistant message |
| `hitl` | `setPendingHitl` — surfaces the `ApprovalDialog` overlay |
| `done` | `setStreaming(false)`, persists messages to history store |
| `error` | `setStreaming(false)` |

---

## Backend Architecture

### Technology Stack

| Concern | Choice |
|---|---|
| Framework | FastAPI 0.115+ |
| Runtime | Uvicorn (ASGI) with `uvicorn[standard]` |
| Python version | 3.11+ |
| Dependency management | `uv` (PEP 517 / `pyproject.toml`) |
| Settings | `pydantic-settings` with `.env` file |
| Azure SDK | `azure-ai-projects` 2.0+, `azure-identity` 1.16+ |
| Agent Framework | `agent-framework` 1.2.2+ (`FoundryAgent`) |
| Auth library | `msal` 1.28+, `PyJWT[crypto]` 2.8+ |
| SSE | `sse-starlette` |
| Observability | `opentelemetry-sdk` + `opentelemetry-instrumentation-fastapi` |

### API Routes

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness probe — returns `{"status":"ok"}` |
| `GET` | `/ready` | Readiness probe — confirms settings are loaded |
| `GET` | `/api/v1/agents` | Lists configured domain agents with descriptions |
| `POST` | `/api/v1/sessions` | Creates a new chat session (returns `session_id`) |
| `GET` | `/api/v1/sessions/{id}` | Retrieves session metadata |
| `DELETE` | `/api/v1/sessions/{id}` | Deletes a session |
| `POST` | `/api/v1/chat/stream` | Main chat endpoint — returns SSE stream |
| `POST` | `/api/v1/chat/hitl` | Resolves a pending Human-in-the-Loop approval |

All `/api/v1/` routes require a valid Entra Bearer token validated by the `validate_token` dependency.

### Middleware Stack (applied in order)

```
Request
  └─ CorrelationIDMiddleware   — propagates / generates X-Correlation-ID header
  └─ RequestLoggingMiddleware  — structured log: method, path, status, duration_ms
  └─ CORSMiddleware            — origins from BACKEND_CORS_ORIGINS env var
  └─ GZipMiddleware            — compresses responses ≥ 1 000 bytes
  └─ Route handler
```

### Security Model

#### JWT Validation

Every protected endpoint runs the `validate_token` FastAPI dependency:

1. Extracts the `Authorization: Bearer <token>` header using `HTTPBearer`.
2. Fetches the Entra JWKS endpoint (`login.microsoftonline.com/{tenant}/discovery/v2.0/keys`) once and caches it for 3 600 seconds.
3. Verifies the signature using RS256.
4. Validates `aud` against both `api://<client-id>` and bare GUID forms (Entra v2 sends either).
5. Validates `iss` against both `login.microsoftonline.com/{tenant}/v2.0` and `sts.windows.net/{tenant}/` issuers.
6. Returns the decoded claims dict (including the raw token for the OBO exchange).

#### On-Behalf-Of (OBO) Token Exchange

When the backend calls Azure AI Foundry, it does so under the user's delegated identity — not the service principal's identity. This enforces user-level RBAC on the Foundry project:

1. The validated user Bearer token is extracted from JWT claims.
2. `get_obo_credential(user_assertion, settings)` constructs an `azure-identity` `OnBehalfOfCredential`.
3. This credential is passed directly to `FoundryAgent`, which uses it when calling the Foundry REST API.
4. Internally, MSAL's `acquire_token_on_behalf_of` exchanges the user assertion for a token scoped to `https://ai.azure.com/.default`.

### Session Management

`SessionService` maintains an in-memory `dict[str, SessionState]` (class-level, shared across all requests within a process). Sessions have a 2-hour TTL; expired entries are evicted lazily on each `create_session` call. Each session stores:

- `session_id` — UUID v4
- `created_at` — UTC datetime
- `agent_name` — optional pre-selected agent
- `hitl_pending` — optional HITL context dict (set when the orchestrator decides a human must approve an action)

> **Note**: This is a single-process in-memory store. For multi-replica deployments, replace with Redis or Azure Cache for Redis.

### Orchestrator Service

`OrchestratorService` is the core execution engine. A new instance is created per request, holding the OBO credential for that user. It caches `FoundryAgent` instances by `(name, version)` within the request to avoid repeated SDK construction.

The `dispatch` coroutine yields SSE events as it progresses through the routing lifecycle:

```
dispatch(query, session_id)
  │
  ├─ yield status("Routing query…")
  ├─ call orchestrator agent → receive JSON plan
  ├─ yield plan(plan)
  │
  ├─ pattern == "hitl"       → store pending HITL, yield hitl event, return
  ├─ pattern == "concurrent" → gather all domain agents in parallel
  │                            → synthesize results
  │                            → yield token(synthesized_text)
  ├─ pattern == "sequential" → chain agents, passing prior output as context
  │                            → yield token(final_text)
  └─ pattern == "single"     → call one domain agent
                               → yield token(result)
```

A 120-second timeout (`asyncio.wait_for`) guards every agent call; timeout errors surface as `error` SSE events.

### Retry Utility

`utils/retry.py` provides an `@async_retry` decorator with configurable `max_attempts` and exponential `backoff_factor`. It wraps any async function, logging each retry attempt before sleeping.

### Observability

`utils/telemetry.py` configures an OpenTelemetry `TracerProvider` with a `BatchSpanProcessor` and `ConsoleSpanExporter`. `FastAPIInstrumentor` auto-instruments all routes, creating spans for every request. In production, the `ConsoleSpanExporter` can be replaced with an OTLP exporter pointing to Azure Monitor.

---

## Microsoft Agent Framework Patterns

FabricMA implements all four orchestration patterns defined by the Microsoft Agent Framework, selected dynamically by the Orchestrator Agent at runtime based on the user's query semantics.

### Pattern 1 — Single Agent

**When used:** The query maps cleanly to exactly one domain (invoices, inventory, or sales).

**Flow:**

```
User query
  → Orchestrator: { "pattern": "single", "agents": ["invoice"] }
  → OrchestratorService.run_single(invoice_agent, query)
  → Fabric Data Agent (invoice) executes SQL
  → Result streamed to user
```

**Example:** "What are the top 10 customers by total invoice value in 2024?"

### Pattern 2 — Concurrent (Fan-Out)

**When used:** The query spans multiple independent domain areas; agent results do not depend on each other.

**Flow:**

```
User query
  → Orchestrator: { "pattern": "concurrent", "agents": ["sales","inventory"] }
  → asyncio.gather(run_single(sales), run_single(inventory))   ← parallel
  → OrchestratorService.synthesize(original_query, {sales: …, inventory: …})
  → Synthesized answer streamed to user
```

**Example:** "Which products had strong sales in 2024 but are running low on inventory?"

The `synthesize` method sends both agent outputs back to the Orchestrator model with an explicit instruction to produce a single coherent answer, citing each source.

### Pattern 3 — Sequential (Chained Context)

**When used:** The output of one agent is the input to the next; earlier results define the parameters for later calls.

**Flow:**

```
User query
  → Orchestrator: { "pattern": "sequential", "agents": ["invoice","sales"] }
  → run_single(invoice_agent, step_1_query)         → result_1
  → run_single(sales_agent, step_2_query + result_1) → result_2 (final answer)
  → Result streamed to user
```

**Example:** "Find customers with overdue AR invoices, then show their 2024 sales — are they still buying?"

Context from the first agent response is appended to the second agent's prompt via: `f"{step_2_query}\n\nContext from previous step:\n{context}"`.

### Pattern 4 — Human-in-the-Loop (HITL)

**When used:** The orchestrator determines that an action requires human approval before execution (e.g. a potentially destructive or high-impact operation like placing a supplier reorder).

**Flow:**

```
User query
  → Orchestrator: { "pattern": "hitl", "agents": [...], "rationale": "…" }
  → OrchestratorService stores hitl_pending in SessionService
  → yield hitl event (session_id + plan) to frontend
  → ApprovalDialog rendered in browser
  → User clicks Approve / Reject
  → POST /api/v1/chat/hitl { session_id, approved }
  → SessionService.resolve_hitl clears the pending state
```

**Example:** "Should we place a supplier reorder for products below threshold?"

The plan including `agents`, `rationale`, and `steps` is surfaced in the approval dialog so the user can make an informed decision.

---

## Orchestrator Agent — Prompt Engineering

The Orchestrator Agent instruction file (`fabric/foundry_agent_instructions/orchestrator_instructions.txt`) enforces a structured output contract:

- **Every response must begin with a fenced JSON block** in the exact schema `{ pattern, agents, rationale, steps }`. This allows `OrchestratorService.parse_plan` to extract the plan with a regex (`re.search(r"```json\s*(\{.*?\})\s*```", ...)`) without fragile string parsing.
- The `steps` array uses a `"Call <agent> agent: <sub-query>"` convention so `_agent_queries_from_steps` can extract per-agent sub-queries for concurrent and sequential patterns.
- The orchestrator explicitly does **not** answer domain questions — it only routes.

### Domain Agent Prompt Design

Each domain agent instruction file enforces:

1. **Data currency anchor** — agents are instructed never to use `CURRENT_DATE` (which returns 2026 and would produce empty results against the 2022–2024 dataset). Explicit year anchors (`use 2024`) are mandated instead.
2. **Scope boundary** — each agent explicitly refuses questions outside its domain and redirects to the correct agent.
3. **Table and field reference** — key schema facts (column names, status values, movement types) are embedded so the LLM generates valid SQL without hallucinating column names.
4. **Response format conventions** — Lead with the direct answer, limit lists to top N, never fabricate placeholder values.

---

## Data Layer — Microsoft Fabric Lakehouse

### Star Schema

The `MeridianSupplyCo` lakehouse uses a standard dimensional model:

**Fact tables**

| Table | Grain | Key metrics |
|---|---|---|
| `FactInvoice` | One row per invoice | `total_amount`, `paid_amount`, `status`, `payment_date_key` |
| `FactInvoiceLine` | One row per line item | `quantity`, `unit_price`, `line_amount` |
| `FactSales` | One row per sale | `extended_amount` (net revenue), `cogs`, `discount_pct` |
| `FactInventorySnapshot` | Daily snapshot per (product, warehouse) | `on_hand_qty` |
| `FactStockMovement` | One row per movement | `quantity_delta`, `movement_type` |

**Dimension tables:** `DimDate`, `DimCustomer`, `DimProduct`, `DimSupplier`, `DimWarehouse`, `DimTerritory`, `DimSalesRep`, `DimCurrency`

### Notebook Pipeline

Fabric notebooks `nb_00` through `nb_12` build the lakehouse end-to-end:

- `nb_00_setup_lakehouse` — provisions the lakehouse
- `nb_01`–`nb_08` — dimension table creation from CSV seed data
- `nb_09`–`nb_11` — fact table construction
- `nb_12_semantic_model` — Power BI semantic model on top

### Fabric Data Agent Connections

Each Foundry domain agent has exactly one `MicrosoftFabricPreviewTool` bound to a `ToolProjectConnection`. This connection is a Foundry project-level connection to the Fabric Data Agent endpoint. The tool allows the domain agent to call Fabric's natural-language-to-SQL engine, which generates and executes Spark SQL against the lakehouse tables.

---

## Agent Provisioning

`scripts/provision_agents.py` uses `azure-ai-projects` to create or re-version all four agents:

1. Resolves each Fabric connection by name (`project.connections.get(conn_name)`).
2. Reads instruction text from `fabric/foundry_agent_instructions/*.txt`.
3. Calls `project.agents.create_version(agent_name, definition)` with a `PromptAgentDefinition` containing the model, instructions, and tools.
4. Domain agents receive a `MicrosoftFabricPreviewTool`; the orchestrator has no tools (it only routes).

Agent versioning is managed by Foundry — the `AZURE_AI_AGENT_VERSION` and `AZURE_AI_AGENT_ORCHESTRATOR_VERSION` environment variables pin which version the backend loads at runtime.

---

## Container and Deployment

### Docker Compose (Local / Dev)

```yaml
services:
  api:   FastAPI backend (port 8000)
  frontend: React SPA served by Nginx (port 5173 → 80)
```

The frontend Nginx config (`frontend/nginx.conf`) proxies `/api/` to the `api` service and serves the React SPA with HTML5 History API fallback (`try_files $uri /index.html`). Gzip is enabled for text, CSS, JS, and JSON responses.

### Production Deployment

The same Docker images can be deployed to:

- **Azure Container Apps** (recommended) — serverless scaling, built-in Entra auth, managed HTTPS
- **Azure Kubernetes Service** — for more complex multi-tenant setups
- **Azure App Service** — for simpler single-container deployments

Health and readiness probes at `/health` and `/ready` are compatible with Kubernetes liveness/readiness probe configuration.

---

## Teams and M365 Copilot Integration

The Orchestrator Agent can be published to Microsoft Teams and M365 Copilot via the Azure AI Foundry portal Agents → Publish workflow. This is in Early Access Preview (as of May 2026). Publishing steps:

1. Register the `Microsoft.BotService` resource provider on the subscription.
2. Publish from Foundry portal → select Teams / M365 Copilot targets.
3. Approve the app in Microsoft 365 Admin Center.
4. Re-apply `agentIdentityId` RBAC on the Foundry project so the published agent retains OBO access to Fabric Data Agents.

---

## Best Practices Implemented

### Security

- **OBO token propagation** — the backend never calls Foundry with its own service principal credentials. Every Foundry call is made under the end user's delegated identity via `OnBehalfOfCredential`, enforcing user-level RBAC on the AI project.
- **JWKS caching** — the `PyJWKClient` is cached via `@lru_cache(maxsize=1)` with a 3 600-second key lifespan to avoid per-request JWKS fetches.
- **Dual-audience and dual-issuer validation** — handles both Entra v1 (`sts.windows.net`) and v2 (`login.microsoftonline.com/…/v2.0`) issuers, and both `api://` URI and bare GUID audience forms.
- **Secrets via environment variables** — all secrets are injected through `.env` / environment variables; no secrets are committed to the repository.
- **CORS scoping** — allowed origins are controlled by the `BACKEND_CORS_ORIGINS` environment variable, not a wildcard.

### Reliability

- **Per-agent 120-second timeout** — every `FoundryAgent.run()` call is wrapped in `asyncio.wait_for`, preventing indefinite hangs.
- **`@async_retry` decorator** — exponential backoff retry utility available for transient failures.
- **Docker healthcheck** — the `api` service has a `curl -f http://localhost:8000/health` healthcheck with 30-second intervals.
- **Session TTL eviction** — stale sessions are lazily evicted to prevent unbounded memory growth.

### Observability

- **Structured request logging** — `RequestLoggingMiddleware` emits a structured log line per request with method, path, status code, and duration in milliseconds.
- **Correlation IDs** — `CorrelationIDMiddleware` propagates or generates `X-Correlation-ID` through every request/response, enabling end-to-end request tracing.
- **OpenTelemetry instrumentation** — `FastAPIInstrumentor` auto-instruments all routes; spans can be exported to Azure Monitor via OTLP.
- **Agent timing logs** — `OrchestratorService` logs `elapsed` time for every agent call and synthesis step at INFO level.
- **Noisy SDK suppression** — `azure.core`, `azure.identity`, and `httpx` loggers are set to WARNING to reduce log noise.

### Developer Experience

- **`uv` for dependency management** — deterministic lock files, fast installs, no virtualenv ceremony.
- **`pydantic-settings`** — configuration is validated and type-safe at startup; missing required variables fail fast with a clear error.
- **`@lru_cache` on settings** — `get_settings()` is called once; the same `Settings` object is reused for the process lifetime.
- **`ruff`** for linting — fast, opinionated, covers `E`, `F`, `I` (isort), and `UP` (pyupgrade) rule sets.
- **Agent version pinning** — `AZURE_AI_AGENT_VERSION` and `AZURE_AI_AGENT_ORCHESTRATOR_VERSION` environment variables allow rolling agent updates without redeploying the backend.

### Frontend

- **Token provider pattern** — a single `setTokenProvider` function is registered in `AppShell` before any child effects fire, ensuring every API call has a valid token.
- **Silent-then-popup token acquisition** — `acquireTokenSilent` is attempted first; only falls back to `acquireTokenPopup` on failure, minimizing user friction.
- **Streaming token accumulation** — `appendToken` in `chatStore` appends to the last assistant message rather than creating a new message per chunk, producing smooth streaming text output.
- **Session title auto-update** — the first 60 characters of the first user message in a session become its history title automatically.

---

## Environment Variable Reference

| Variable | Required | Description |
|---|---|---|
| `AZURE_TENANT_ID` | Yes | Microsoft Entra tenant ID |
| `AZURE_CLIENT_ID` | Yes | Backend app registration client ID |
| `AZURE_CLIENT_SECRET` | Yes | Backend app registration client secret |
| `AZURE_AUDIENCE` | Yes | Token audience (`api://<client-id>` or bare GUID) |
| `AZURE_AI_PROJECT_ENDPOINT` | Yes | Azure AI Foundry project endpoint URL |
| `AZURE_AI_MODEL_STANDARD` | No | Model name for domain agents (default: `gpt-4.1-mini`) |
| `AZURE_AI_MODEL_THINKING` | No | Model name for orchestrator (default: `o4-mini`) |
| `AZURE_AI_AGENT_INVOICE_NAME` | Yes | Foundry agent name for the Invoice agent |
| `AZURE_AI_AGENT_INVENTORY_NAME` | Yes | Foundry agent name for the Inventory agent |
| `AZURE_AI_AGENT_SALES_NAME` | Yes | Foundry agent name for the Sales agent |
| `AZURE_AI_AGENT_ORCHESTRATOR_NAME` | Yes | Foundry agent name for the Orchestrator agent |
| `AZURE_AI_AGENT_VERSION` | No | Domain agent version to load (default: `1`) |
| `AZURE_AI_AGENT_ORCHESTRATOR_VERSION` | No | Orchestrator agent version to load (default: `2`) |
| `FABRIC_CONNECTION_INVOICE` | Yes | Foundry connection name for the Invoice Fabric Data Agent |
| `FABRIC_CONNECTION_INVENTORY` | Yes | Foundry connection name for the Inventory Fabric Data Agent |
| `FABRIC_CONNECTION_SALES` | Yes | Foundry connection name for the Sales Fabric Data Agent |
| `BACKEND_CORS_ORIGINS` | No | Comma-separated list of allowed CORS origins |
| `LOG_LEVEL` | No | Python logging level (default: `INFO`) |
| `VITE_API_URL` | Yes (frontend) | Backend base URL used by the SPA |
| `VITE_AZURE_CLIENT_ID` | Yes (frontend) | SPA app registration client ID |
| `VITE_AZURE_TENANT_ID` | Yes (frontend) | Microsoft Entra tenant ID |
| `VITE_AZURE_BACKEND_SCOPE` | Yes (frontend) | Backend API scope for MSAL token acquisition |
