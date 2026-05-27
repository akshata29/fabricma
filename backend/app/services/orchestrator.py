import asyncio
import json
import logging
import re
import time
from collections.abc import AsyncGenerator

from agent_framework_foundry import FoundryAgent
from azure.identity import AzureCliCredential, ClientSecretCredential

from app.config import Settings
from app.services.auth_service import get_obo_credential
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)
_AGENT_TIMEOUT_SEC = 120


class OrchestratorService:
    def __init__(self, settings: Settings, user_token: str | None = None) -> None:
        self._settings = settings
        # When a user token is supplied, delegate calls on behalf of that user (OBO).
        # When absent (e.g. the Teams bot calling without SSO), fall back to the
        # application's own client-secret credential so the bot can still reach Foundry.
        if user_token:
            self._credential = get_obo_credential(user_token, settings)
        elif not settings.teams_app_id:
            # Dev / emulator mode: no bot app ID means we're running locally
            # without a registered Azure Bot.  Use the developer's Azure CLI
            # identity (`az login`) which already has delegated Fabric access,
            # matching what OBO provides in production.
            self._credential = AzureCliCredential()
        else:
            # Production bot identity: service principal with client secret.
            # In real Teams deployments OBO is always present, so this path
            # only runs for background/proactive scenarios.
            self._credential = ClientSecretCredential(
                tenant_id=settings.azure_tenant_id,
                client_id=settings.azure_client_id,
                client_secret=settings.azure_client_secret,
            )
        self._session_service = SessionService()
        # Cache FoundryAgent instances by (name, version) to avoid repeated construction.
        self._agent_cache: dict[str, FoundryAgent] = {}

    def _make_maf_agent(self, agent_name: str, *, orchestrator: bool = False) -> FoundryAgent:
        version = (
            self._settings.azure_ai_agent_orchestrator_version
            if orchestrator
            else self._settings.azure_ai_agent_version
        )
        cache_key = f"{agent_name}:{version}"
        if cache_key not in self._agent_cache:
            self._agent_cache[cache_key] = FoundryAgent(
                project_endpoint=self._settings.azure_ai_project_endpoint,
                credential=self._credential,
                agent_name=agent_name,
                agent_version=version,
                allow_preview=True,
            )
        return self._agent_cache[cache_key]

    async def run_single(self, agent_name: str, query: str) -> str:
        agent = self._make_maf_agent(agent_name)
        logger.info("agent call started | agent=%s", agent_name)
        t = time.perf_counter()
        try:
            result = await asyncio.wait_for(agent.run(query), timeout=_AGENT_TIMEOUT_SEC)
        except asyncio.TimeoutError:
            logger.error("agent call timed out | agent=%s elapsed=%.1fs", agent_name, _AGENT_TIMEOUT_SEC)
            raise RuntimeError(f"Agent '{agent_name}' timed out after {_AGENT_TIMEOUT_SEC}s")
        logger.info("agent call done | agent=%s elapsed=%.1fs", agent_name, time.perf_counter() - t)
        return str(result)

    async def run_concurrent(
        self, agent_names: list[str], queries: list[str]
    ) -> dict[str, str]:
        results = await asyncio.gather(
            *(self.run_single(name, q) for name, q in zip(agent_names, queries))
        )
        return dict(zip(agent_names, results))

    async def run_sequential(self, agent_names: list[str], queries: list[str]) -> str:
        context = ""
        last_response = ""
        for name, q in zip(agent_names, queries):
            full_query = f"{q}\n\nContext from previous step:\n{context}" if context else q
            last_response = await self.run_single(name, full_query)
            context = last_response
        return last_response

    async def synthesize(self, original_query: str, agent_results: dict[str, str]) -> str:
        """Ask the orchestrator to synthesize collected agent results into one answer."""
        parts = "\n\n".join(
            f"[{agent} agent response]\n{result}" for agent, result in agent_results.items()
        )
        synthesis_prompt = (
            f"Original user query: {original_query}\n\n"
            f"The following responses were collected from domain agents:\n\n{parts}\n\n"
            "Synthesize these into a single, coherent answer for the user. "
            "Do NOT output a JSON plan block — only the synthesized answer."
        )
        agent = self._make_maf_agent(
            self._settings.azure_ai_agent_orchestrator_name, orchestrator=True
        )
        logger.info("synthesis call started")
        t = time.perf_counter()
        try:
            result = await asyncio.wait_for(agent.run(synthesis_prompt), timeout=_AGENT_TIMEOUT_SEC)
        except asyncio.TimeoutError:
            logger.error("synthesis timed out after %.1fs", _AGENT_TIMEOUT_SEC)
            # Fall back to concatenated results
            return "\n\n".join(f"**{k}**: {v}" for k, v in agent_results.items())
        logger.info("synthesis done | elapsed=%.1fs", time.perf_counter() - t)
        return str(result)

    async def parse_plan(self, plan_text: str) -> dict:
        match = re.search(r"```json\s*(\{.*?\})\s*```", plan_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        return {
            "pattern": "single",
            "agents": [],
            "rationale": "Could not parse plan",
            "steps": [],
        }

    def _agent_queries_from_steps(
        self, steps: list[str], agents: list[str], fallback_query: str
    ) -> list[str]:
        """
        Extract per-agent sub-queries from the plan steps list.
        Each step that starts with "Call <agent> agent:" is matched to that agent.
        If no matching step is found, the full original query is used as fallback.
        """
        queries = []
        for agent in agents:
            matched = None
            prefix = f"call {agent} agent:"
            for step in steps:
                if step.lower().startswith(prefix):
                    matched = step[len(prefix):].strip()
                    break
            queries.append(matched if matched else fallback_query)
        return queries

    async def dispatch(self, query: str, session_id: str) -> AsyncGenerator[dict, None]:
        yield {"type": "status", "data": {"message": "Routing query..."}}

        orch_agent = self._make_maf_agent(
            self._settings.azure_ai_agent_orchestrator_name, orchestrator=True
        )
        logger.info("orchestrator call started | session=%s query=%.80s", session_id, query)
        t = time.perf_counter()
        try:
            plan_text = await asyncio.wait_for(
                orch_agent.run(query), timeout=_AGENT_TIMEOUT_SEC
            )
        except asyncio.TimeoutError:
            logger.error("orchestrator timed out | session=%s elapsed=%.1fs", session_id, _AGENT_TIMEOUT_SEC)
            yield {"type": "error", "data": {"message": "Orchestrator timed out. Please try again."}}
            return
        logger.info("orchestrator call done | session=%s elapsed=%.1fs", session_id, time.perf_counter() - t)

        plan = await self.parse_plan(str(plan_text))
        yield {"type": "plan", "data": plan}

        pattern = plan.get("pattern", "single")
        agents = plan.get("agents", [])

        agent_name_map = {
            "invoice": self._settings.azure_ai_agent_invoice_name,
            "inventory": self._settings.azure_ai_agent_inventory_name,
            "sales": self._settings.azure_ai_agent_sales_name,
        }
        resolved_agents = [
            agent_name_map.get(a, a) for a in agents if a in agent_name_map
        ]

        if pattern == "hitl":
            self._session_service.store_hitl_pending(
                session_id, {"query": query, "plan": plan}
            )
            yield {"type": "hitl", "data": {"session_id": session_id, "plan": plan}}
            return

        if pattern == "concurrent" and resolved_agents:
            agent_queries = self._agent_queries_from_steps(
                plan.get("steps", []), agents, query
            )
            resolved_queries = [
                agent_queries[i] for i, a in enumerate(agents) if a in agent_name_map
            ]
            yield {"type": "status", "data": {"message": f"Running {', '.join(agents)} agents in parallel..."}}
            results = await self.run_concurrent(resolved_agents, resolved_queries)
            yield {"type": "status", "data": {"message": "Synthesizing results..."}}
            synthesized = await self.synthesize(query, results)
            yield {"type": "token", "data": {"text": synthesized}}
        elif pattern == "sequential" and resolved_agents:
            agent_queries = self._agent_queries_from_steps(
                plan.get("steps", []), agents, query
            )
            resolved_queries = [
                agent_queries[i] for i, a in enumerate(agents) if a in agent_name_map
            ]
            yield {"type": "status", "data": {"message": f"Running {', '.join(agents)} agents in sequence..."}}
            result = await self.run_sequential(resolved_agents, resolved_queries)
            yield {"type": "token", "data": {"text": result}}
        elif resolved_agents:
            yield {"type": "status", "data": {"message": f"Calling {agents[0]} agent..."}}
            result = await self.run_single(resolved_agents[0], query)
            yield {"type": "token", "data": {"text": result}}
        else:
            yield {"type": "token", "data": {"text": "No domain agents selected."}}

        yield {"type": "done", "data": {"session_id": session_id}}

    async def dispatch_with_plan(
        self, query: str, session_id: str, plan: dict
    ) -> AsyncGenerator[dict, None]:
        """Execute a pre-approved routing plan without re-routing through the orchestrator.

        Used after HITL approval so the previously-chosen plan runs directly,
        avoiding a second orchestrator call that might re-trigger the hitl pattern.
        """
        yield {"type": "plan", "data": plan}

        pattern = plan.get("pattern", "single")
        agents = plan.get("agents", [])

        agent_name_map = {
            "invoice": self._settings.azure_ai_agent_invoice_name,
            "inventory": self._settings.azure_ai_agent_inventory_name,
            "sales": self._settings.azure_ai_agent_sales_name,
        }
        resolved_agents = [
            agent_name_map.get(a, a) for a in agents if a in agent_name_map
        ]

        if pattern == "concurrent" and resolved_agents:
            agent_queries = self._agent_queries_from_steps(
                plan.get("steps", []), agents, query
            )
            resolved_queries = [
                agent_queries[i] for i, a in enumerate(agents) if a in agent_name_map
            ]
            yield {"type": "status", "data": {"message": f"Running {', '.join(agents)} agents in parallel..."}}
            results = await self.run_concurrent(resolved_agents, resolved_queries)
            yield {"type": "status", "data": {"message": "Synthesizing results..."}}
            synthesized = await self.synthesize(query, results)
            yield {"type": "token", "data": {"text": synthesized}}
        elif pattern == "sequential" and resolved_agents:
            agent_queries = self._agent_queries_from_steps(
                plan.get("steps", []), agents, query
            )
            resolved_queries = [
                agent_queries[i] for i, a in enumerate(agents) if a in agent_name_map
            ]
            yield {"type": "status", "data": {"message": f"Running {', '.join(agents)} agents in sequence..."}}
            result = await self.run_sequential(resolved_agents, resolved_queries)
            yield {"type": "token", "data": {"text": result}}
        elif resolved_agents:
            yield {"type": "status", "data": {"message": f"Calling {agents[0]} agent..."}}
            result = await self.run_single(resolved_agents[0], query)
            yield {"type": "token", "data": {"text": result}}
        else:
            yield {"type": "token", "data": {"text": "No domain agents selected."}}

        yield {"type": "done", "data": {"session_id": session_id}}
