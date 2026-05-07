import { create } from 'zustand'
import type { Message, OrchestratorPlan, HitlData } from '@/types/chat'
import type { HistorySession } from './historyStore'

interface ChatState {
  messages: Message[]
  isStreaming: boolean
  statusMessage: string
  pendingHitl: HitlData | null
  currentPlan: OrchestratorPlan | null
  addMessage: (msg: Message) => void
  appendToken: (text: string) => void
  setStreaming: (v: boolean) => void
  setStatusMessage: (msg: string) => void
  setPendingHitl: (data: HitlData | null) => void
  setCurrentPlan: (plan: OrchestratorPlan | null) => void
  clearMessages: () => void
  loadSession: (session: HistorySession) => void
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  statusMessage: 'Thinking...',
  pendingHitl: null,
  currentPlan: null,

  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),

  appendToken: (text) =>
    set((s) => {
      const messages = [...s.messages]
      const last = messages[messages.length - 1]
      if (last && last.role === 'assistant') {
        messages[messages.length - 1] = { ...last, content: last.content + text }
      } else {
        messages.push({
          id: crypto.randomUUID(),
          role: 'assistant',
          content: text,
          timestamp: new Date(),
        })
      }
      return { messages }
    }),

  setStreaming: (isStreaming) => set({ isStreaming }),
  setStatusMessage: (statusMessage) => set({ statusMessage }),
  setPendingHitl: (pendingHitl) => set({ pendingHitl }),
  setCurrentPlan: (currentPlan) => set({ currentPlan }),
  clearMessages: () => set({ messages: [], currentPlan: null, pendingHitl: null, statusMessage: 'Thinking...' }),
  loadSession: (session) =>
    set({
      messages: session.messages.map((m) => ({
        ...m,
        timestamp: new Date(m.timestamp),
      })),
      currentPlan: null,
      pendingHitl: null,
      isStreaming: false,
      statusMessage: 'Thinking...',
    }),
}))
