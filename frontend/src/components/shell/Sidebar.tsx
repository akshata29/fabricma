import { Plus } from 'lucide-react'
import { useAgents } from '@/hooks/useAgents'
import { AgentSelector } from '@/components/agents/AgentSelector'
import { SessionHistory } from './SessionHistory'
import { useSessionStore } from '@/store/sessionStore'
import { useChatStore } from '@/store/chatStore'
import { createSession } from '@/api/sessions'
import { useHistoryStore } from '@/store/historyStore'

export function Sidebar() {
  const { agents } = useAgents()
  const { setSessionId } = useSessionStore()
  const { clearMessages } = useChatStore()
  const { upsertSession } = useHistoryStore()

  const handleNewChat = async () => {
    clearMessages()
    try {
      const s = await createSession()
      setSessionId(s.session_id)
      upsertSession(
        s.session_id,
        `Session ${new Date(s.created_at).toLocaleString()}`,
        s.created_at,
      )
    } catch (err) {
      console.error('Failed to create new session:', err)
    }
  }

  return (
    <aside className="flex w-64 flex-col border-r border-border bg-card px-4 py-6 gap-4">
      <div>
        <h2 className="text-lg font-semibold text-foreground">FabricMA</h2>
        <p className="text-xs text-muted-foreground">Meridian Supply Co.</p>
      </div>
      <button
        onClick={handleNewChat}
        className="flex items-center gap-2 rounded-lg border border-border px-3 py-2 text-xs text-foreground transition-colors hover:bg-accent"
      >
        <Plus className="h-3.5 w-3.5" />
        New chat
      </button>
      <AgentSelector agents={agents} />
      <SessionHistory />
    </aside>
  )
}
