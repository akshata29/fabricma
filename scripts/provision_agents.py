"""
scripts/provision_agents.py
Creates (or re-versions) all four Foundry agents using Responses API v2 create_version.
Usage: python scripts/provision_agents.py
Requires: .env at repo root, Fabric connections already created in Foundry portal.
Run from repo root: cd backend && uv run python ../scripts/provision_agents.py
"""
import os
from pathlib import Path
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    MicrosoftFabricPreviewTool,
    FabricDataAgentToolParameters,
    ToolProjectConnection,
)
from dotenv import load_dotenv

load_dotenv()

project = AIProjectClient(
    endpoint=os.environ["AZURE_AI_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

INSTRUCTIONS_DIR = Path(__file__).parent.parent / "fabric" / "foundry_agent_instructions"

DOMAIN_AGENTS = [
    ("AZURE_AI_AGENT_INVOICE_NAME",   "FABRIC_CONNECTION_INVOICE",   "invoice_agent_instructions.txt"),
    ("AZURE_AI_AGENT_INVENTORY_NAME", "FABRIC_CONNECTION_INVENTORY", "inventory_agent_instructions.txt"),
    ("AZURE_AI_AGENT_SALES_NAME",     "FABRIC_CONNECTION_SALES",     "sales_agent_instructions.txt"),
]

for name_env, conn_env, instr_file in DOMAIN_AGENTS:
    conn = project.connections.get(os.environ[conn_env])
    instructions = (INSTRUCTIONS_DIR / instr_file).read_text()
    agent = project.agents.create_version(
        agent_name=os.environ[name_env],
        definition=PromptAgentDefinition(
            model=os.environ["AZURE_AI_MODEL_STANDARD"],
            instructions=instructions,
            tools=[MicrosoftFabricPreviewTool(
                fabric_dataagent_preview=FabricDataAgentToolParameters(
                    project_connections=[ToolProjectConnection(project_connection_id=conn.id)]
                )
            )],
        ),
    )
    print(f"  Created {agent.name}:{agent.version}")

# Orchestrator — standard model, no Fabric tool
instructions = (INSTRUCTIONS_DIR / "orchestrator_instructions.txt").read_text()
orch = project.agents.create_version(
    agent_name=os.environ["AZURE_AI_AGENT_ORCHESTRATOR_NAME"],
    definition=PromptAgentDefinition(
        model=os.environ["AZURE_AI_MODEL_STANDARD"],
        instructions=instructions,
    ),
)
print(f"  Created orchestrator {orch.name}:{orch.version}")
