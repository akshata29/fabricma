import { apiClient } from './client'

export async function submitHitlApproval(
  sessionId: string,
  approved: boolean,
  reason?: string,
): Promise<void> {
  await apiClient.post('/api/v1/chat/hitl', { session_id: sessionId, approved, reason })
}
