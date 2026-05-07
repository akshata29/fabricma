import { useAuthToken } from '@/lib/auth'
import { setTokenProvider } from '@/api/client'
import { Sidebar } from './Sidebar'
import { ChatPanel } from '@/components/chat/ChatPanel'

export function AppShell() {
  const { getToken } = useAuthToken()

  // Set synchronously during render so the provider is in place
  // before any child useEffect fires its API request.
  setTokenProvider(getToken)

  return (
    <div className="flex h-screen overflow-hidden bg-background text-foreground">
      <Sidebar />
      <main className="flex flex-1 flex-col overflow-hidden">
        <ChatPanel />
      </main>
    </div>
  )
}
