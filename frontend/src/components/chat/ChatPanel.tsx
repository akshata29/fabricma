import { TopBar } from '@/components/shell/TopBar'
import { MessageList } from './MessageList'
import { InputBar } from './InputBar'
import { StreamingIndicator } from './StreamingIndicator'
import { ApprovalDialog } from '@/components/hitl/ApprovalDialog'
import { useChatStore } from '@/store/chatStore'
import { useSession } from '@/hooks/useSession'

export function ChatPanel() {
  const { isStreaming, pendingHitl } = useChatStore()
  const { sessionId } = useSession()

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <TopBar />
      <div className="flex flex-1 flex-col overflow-hidden p-4 gap-4">
        <MessageList />
        {isStreaming && <StreamingIndicator />}
        <InputBar sessionId={sessionId ?? ''} />
      </div>
      {pendingHitl && <ApprovalDialog data={pendingHitl} />}
    </div>
  )
}
