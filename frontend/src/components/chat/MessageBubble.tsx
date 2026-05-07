import { memo } from 'react'
import { Bot } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Message } from '@/types/chat'
import { PlanPreview } from '@/components/hitl/PlanPreview'
import { MarkdownText } from './MarkdownText'

interface Props {
  message: Message
}

export const MessageBubble = memo(function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex gap-3 items-end', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full bg-primary/10 ring-1 ring-primary/20">
          <Bot className="h-3.5 w-3.5 text-primary" />
        </div>
      )}
      <div
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-3 shadow-sm',
          isUser
            ? 'rounded-br-sm bg-primary text-primary-foreground'
            : 'rounded-bl-sm border border-border bg-card text-foreground',
        )}
      >
        {message.plan && <PlanPreview plan={message.plan} />}
        {isUser ? (
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</p>
        ) : (
          <MarkdownText text={message.content} />
        )}
        <time className={cn('mt-2 block text-[10px] opacity-50', isUser ? 'text-right' : '')}>
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </time>
      </div>
    </div>
  )
})
