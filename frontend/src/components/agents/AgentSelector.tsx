import { useAgentStore } from '@/store/agentStore'
import { AgentStatusBadge } from './AgentStatusBadge'
import type { AgentInfo } from '@/types/agent'

interface Props {
  agents: AgentInfo[]
}

export function AgentSelector({ agents }: Props) {
  const { selectedAgents, toggleAgent } = useAgentStore()

  return (
    <div className="flex flex-col gap-2">
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Agents</p>
      {agents.map((agent) => (
        <button
          key={agent.name}
          onClick={() => toggleAgent(agent.name)}
          className="flex items-center gap-2 rounded-md p-2 text-left hover:bg-accent transition-colors"
        >
          <AgentStatusBadge agent={agent} selected={selectedAgents.includes(agent.name)} />
        </button>
      ))}
    </div>
  )
}
