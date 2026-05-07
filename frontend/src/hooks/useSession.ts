import { useEffect, useRef } from 'react'
import { createSession } from '@/api/sessions'
import { useSessionStore } from '@/store/sessionStore'
import { useHistoryStore } from '@/store/historyStore'

export function useSession() {
  const { sessionId, setSessionId } = useSessionStore()
  const { upsertSession } = useHistoryStore()
  const creating = useRef(false)

  useEffect(() => {
    if (sessionId || creating.current) return
    creating.current = true
    createSession()
      .then((s) => {
        setSessionId(s.session_id)
        upsertSession(
          s.session_id,
          `Session ${new Date(s.created_at).toLocaleString()}`,
          s.created_at,
        )
      })
      .catch(console.error)
      .finally(() => { creating.current = false })
  }, [sessionId, setSessionId, upsertSession])

  return { sessionId }
}
