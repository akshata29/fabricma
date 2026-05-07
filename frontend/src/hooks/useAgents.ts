import { useEffect, useRef } from 'react'
import { getAgents } from '@/api/agents'
import { useAgentStore } from '@/store/agentStore'

export function useAgents() {
  const { agents, setAgents } = useAgentStore()
  const fetching = useRef(false)

  useEffect(() => {
    // Skip if agents are already loaded or a fetch is already in flight.
    if (agents.length > 0 || fetching.current) return
    fetching.current = true
    getAgents()
      .then((r) => setAgents(r.agents))
      .catch(console.error)
      .finally(() => { fetching.current = false })
  }, [agents.length, setAgents])

  return { agents }
}
