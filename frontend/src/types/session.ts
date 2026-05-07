export interface SessionCreate {
  agent_name?: string
}

export interface SessionResponse {
  session_id: string
  created_at: string
  agent_name?: string
}
