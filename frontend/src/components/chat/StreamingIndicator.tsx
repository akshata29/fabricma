import { Loader2 } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'

export function StreamingIndicator() {
  const { statusMessage } = useChatStore()
  return (
    <div className="flex items-center gap-2.5 px-2 py-1">
      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-primary/10">
        <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
      </div>
      <span className="text-xs text-muted-foreground">{statusMessage}</span>
    </div>
  )
}
