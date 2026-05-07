import { useState, useRef, KeyboardEvent } from 'react'
import { Send } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import { useChatStream } from '@/hooks/useChatStream'

interface Props {
  sessionId: string
}

export function InputBar({ sessionId }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const { isStreaming, addMessage } = useChatStore()
  const { sendMessage } = useChatStream()

  const handleSend = async () => {
    const query = value.trim()
    if (!query || isStreaming || !sessionId) return
    setValue('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    })
    await sendMessage(query, sessionId)
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value)
    const ta = e.target
    ta.style.height = 'auto'
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const canSend = !isStreaming && !!value.trim() && !!sessionId

  return (
    <div className="flex gap-2 items-end rounded-2xl border border-border bg-card px-3 py-2 shadow-sm transition-shadow focus-within:ring-1 focus-within:ring-ring">
      <textarea
        ref={textareaRef}
        className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder:text-muted-foreground focus:outline-none disabled:opacity-50 min-h-[2rem] max-h-40"
        rows={1}
        placeholder="Ask about invoices, inventory, or sales… (Shift+Enter to send)"
        value={value}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={isStreaming}
      />
      <button
        onClick={handleSend}
        disabled={!canSend}
        className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground transition-all hover:opacity-90 disabled:opacity-30"
        aria-label="Send"
      >
        <Send className="h-4 w-4" />
      </button>
    </div>
  )
}
