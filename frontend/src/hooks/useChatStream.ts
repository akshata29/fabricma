import { useAuthToken } from '@/lib/auth'
import { useChatStore } from '@/store/chatStore'
import { useHistoryStore } from '@/store/historyStore'
import { SSE_EVENTS } from '@/lib/constants'
import type { OrchestratorPlan, HitlData } from '@/types/chat'

export function useChatStream() {
  const { getToken } = useAuthToken()
  const { appendToken, setStreaming, setStatusMessage, setPendingHitl, setCurrentPlan } = useChatStore()
  const { saveMessages, upsertSession, sessions } = useHistoryStore()

  const sendMessage = async (query: string, sessionId: string) => {
    const token = await getToken()
    setStreaming(true)

    // Update session title from the first user message if still default.
    const existing = sessions.find((s) => s.sessionId === sessionId)
    if (existing && existing.messages.length === 0) {
      const shortTitle = query.length > 60 ? query.slice(0, 57) + '...' : query
      useHistoryStore.setState((s) => ({
        sessions: s.sessions.map((h) =>
          h.sessionId === sessionId ? { ...h, title: shortTitle } : h,
        ),
      }))
    }

    let response: Response
    try {
      response = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ query, session_id: sessionId }),
      })
    } catch (err) {
      console.error('SSE fetch failed:', err)
      setStreaming(false)
      return
    }

    if (!response.ok || !response.body) {
      console.error('SSE bad response:', response.status)
      setStreaming(false)
      return
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let currentEvent = ''

    const persist = () => {
      const { messages } = useChatStore.getState()
      saveMessages(sessionId, messages)
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (line.startsWith('event:')) {
            currentEvent = line.slice(6).trim()
          } else if (line.startsWith('data:')) {
            const rawData = line.slice(5).trim()
            if (!rawData) continue
            try {
              const data = JSON.parse(rawData)
              switch (currentEvent) {
                case SSE_EVENTS.PLAN:
                  setCurrentPlan(data as OrchestratorPlan)
                  break
                case SSE_EVENTS.TOKEN:
                  appendToken(data.text as string)
                  break
                case SSE_EVENTS.STATUS:
                  setStatusMessage(data.message as string)
                  break
                case SSE_EVENTS.HITL:
                  setPendingHitl(data as HitlData)
                  setStreaming(false)
                  persist()
                  return
                case SSE_EVENTS.DONE:
                  setStreaming(false)
                  persist()
                  return
                case SSE_EVENTS.ERROR:
                  console.error('SSE error event:', data)
                  setStreaming(false)
                  return
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e, rawData)
            }
            currentEvent = ''
          }
        }
      }
    } finally {
      reader.releaseLock()
      setStreaming(false)
    }
  }

  return { sendMessage }
}
