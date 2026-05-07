import { useMsal } from '@azure/msal-react'
import { LogOut, MessageSquare } from 'lucide-react'
import { useSessionStore } from '@/store/sessionStore'
import { useHistoryStore } from '@/store/historyStore'

export function TopBar() {
  const { instance, accounts } = useMsal()
  const account = accounts[0]
  const { sessionId } = useSessionStore()
  const { sessions } = useHistoryStore()

  const currentSession = sessions.find((s) => s.sessionId === sessionId)
  const title = currentSession?.title ?? 'New Chat'

  const initials = account?.name
    ? account.name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : (account?.username?.slice(0, 2).toUpperCase() ?? '?')

  return (
    <header className="flex items-center justify-between border-b border-border bg-card px-4 py-2.5">
      <div className="flex items-center gap-2 min-w-0">
        <MessageSquare className="h-4 w-4 flex-shrink-0 text-primary" />
        <span className="truncate text-sm font-medium text-foreground max-w-xs">{title}</span>
      </div>
      <div className="flex items-center gap-3">
        {account && (
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary ring-1 ring-primary/20">
              {initials}
            </div>
            <span className="hidden text-xs text-muted-foreground sm:block">{account.username}</span>
          </div>
        )}
        <button
          onClick={() => instance.logoutPopup()}
          className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <LogOut className="h-3.5 w-3.5" />
          <span className="hidden sm:block">Sign out</span>
        </button>
      </div>
    </header>
  )
}
