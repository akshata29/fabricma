import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Message } from '@/types/chat'

export interface HistorySession {
  sessionId: string
  title: string
  createdAt: string // ISO string (serialisable)
  messages: Array<Omit<Message, 'timestamp'> & { timestamp: string }>
}

interface HistoryState {
  sessions: HistorySession[]
  upsertSession: (sessionId: string, title: string, createdAt: string) => void
  saveMessages: (sessionId: string, messages: Message[]) => void
  removeSession: (sessionId: string) => void
}

export const useHistoryStore = create<HistoryState>()(
  persist(
    (set) => ({
      sessions: [],

      upsertSession: (sessionId, title, createdAt) =>
        set((s) => {
          const exists = s.sessions.some((h) => h.sessionId === sessionId)
          if (exists) return s
          return {
            sessions: [
              { sessionId, title, createdAt, messages: [] },
              ...s.sessions,
            ],
          }
        }),

      saveMessages: (sessionId, messages) =>
        set((s) => ({
          sessions: s.sessions.map((h) =>
            h.sessionId !== sessionId
              ? h
              : {
                  ...h,
                  messages: messages.map((m) => ({
                    ...m,
                    timestamp: m.timestamp instanceof Date
                      ? m.timestamp.toISOString()
                      : String(m.timestamp),
                  })),
                },
          ),
        })),

      removeSession: (sessionId) =>
        set((s) => ({
          sessions: s.sessions.filter((h) => h.sessionId !== sessionId),
        })),
    }),
    { name: 'fabricma-history' },
  ),
)
