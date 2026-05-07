import { MessageSquare, Trash2 } from 'lucide-react'
import { useHistoryStore } from '@/store/historyStore'
import { useChatStore } from '@/store/chatStore'
import { useSessionStore } from '@/store/sessionStore'
import { deleteSession } from '@/api/sessions'
import { cn } from '@/lib/utils'

export function SessionHistory() {
  const { sessions, removeSession } = useHistoryStore()
  const { loadSession, clearMessages } = useChatStore()
  const { sessionId, setSessionId } = useSessionStore()

  if (sessions.length === 0) return null

  const handleRestore = (session: typeof sessions[0]) => {
    if (session.sessionId === sessionId) return
    setSessionId(session.sessionId)
    loadSession(session)
  }

  const handleDelete = async (e: React.MouseEvent, targetId: string) => {
    e.stopPropagation()
    // Best-effort backend deletion; ignore 404 (already evicted by TTL).
    deleteSession(targetId).catch(() => {})
    removeSession(targetId)
    // If we deleted the active session, clear the view and reset to no active session.
    if (targetId === sessionId) {
      clearMessages()
      setSessionId(null)
    }
  }

  return (
    <div className="mt-auto flex flex-col gap-1 border-t border-border pt-4">
      <p className="mb-1 px-1 text-xs font-medium uppercase tracking-wider text-muted-foreground">
        History
      </p>
      <div className="flex max-h-52 flex-col gap-0.5 overflow-y-auto">
        {sessions.map((s) => (
          <div
            key={s.sessionId}
            className={cn(
              'group flex cursor-pointer items-center gap-2 rounded-lg px-2 py-1.5 transition-colors hover:bg-accent',
              s.sessionId === sessionId && 'bg-accent',
            )}
            onClick={() => handleRestore(s)}
          >
            <MessageSquare
              className={cn(
                'h-3.5 w-3.5 flex-shrink-0 transition-colors',
                s.sessionId === sessionId ? 'text-primary' : 'text-muted-foreground',
              )}
            />
            <span className="flex-1 truncate text-xs text-foreground">{s.title}</span>
            <button
              onClick={(e) => handleDelete(e, s.sessionId)}
              className="hidden h-4 w-4 items-center justify-center rounded text-muted-foreground transition-colors hover:text-destructive group-hover:flex"
              aria-label="Delete session"
            >
              <Trash2 className="h-3 w-3" />
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
