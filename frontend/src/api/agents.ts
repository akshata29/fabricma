import { apiClient } from './client'
import type { AgentListResponse } from '@/types/agent'

export async function getAgents(): Promise<AgentListResponse> {
  const { data } = await apiClient.get<AgentListResponse>('/api/v1/agents')
  return data
}
