import { apiClient } from './client'
import type { SessionCreate, SessionResponse } from '@/types/session'

export async function createSession(body: SessionCreate = {}): Promise<SessionResponse> {
  const { data } = await apiClient.post<SessionResponse>('/api/v1/sessions', body)
  return data
}

export async function getSession(id: string): Promise<SessionResponse> {
  const { data } = await apiClient.get<SessionResponse>(`/api/v1/sessions/${id}`)
  return data
}

export async function deleteSession(id: string): Promise<void> {
  await apiClient.delete(`/api/v1/sessions/${id}`)
}
