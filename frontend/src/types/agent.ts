export interface AgentInfo {
  name: string
  description: string
  status: 'available' | 'busy' | 'offline'
}

export interface AgentListResponse {
  agents: AgentInfo[]
}
