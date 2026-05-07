export interface OrchestratorPlan {
  pattern: 'single' | 'sequential' | 'concurrent' | 'hitl'
  agents: string[]
  rationale: string
  steps: string[]
}

export interface HitlData {
  session_id: string
  plan: OrchestratorPlan
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  plan?: OrchestratorPlan
}

export interface ChatRequest {
  query: string
  session_id: string
  agent_names?: string[]
}
