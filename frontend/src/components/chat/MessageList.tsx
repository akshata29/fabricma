import { useEffect, useRef } from 'react'
import { useChatStore } from '@/store/chatStore'
import { MessageBubble } from './MessageBubble'
import { EmptyState } from './EmptyState'

export function MessageList() {
  const { messages } = useChatStore()
  const bottomRef = useRef<HTMLDivElement>(null)
  const prevLengthRef = useRef(0)

  useEffect(() => {
    // Only scroll when a new message is added, not on every streaming token append.
    if (messages.length > prevLengthRef.current) {
      prevLengthRef.current = messages.length
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 flex-col overflow-y-auto">
        <EmptyState />
      </div>
    )
  }

  return (
    <div className="flex flex-1 flex-col gap-4 overflow-y-auto px-2 py-2">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  )
}
