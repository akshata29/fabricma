import { create } from 'zustand'
import type { AgentInfo } from '@/types/agent'

interface AgentState {
  agents: AgentInfo[]
  selectedAgents: string[]
  setAgents: (agents: AgentInfo[]) => void
  toggleAgent: (name: string) => void
  clearSelection: () => void
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  selectedAgents: [],
  setAgents: (agents) => set({ agents }),
  toggleAgent: (name) =>
    set((s) => ({
      selectedAgents: s.selectedAgents.includes(name)
        ? s.selectedAgents.filter((n) => n !== name)
        : [...s.selectedAgents, name],
    })),
  clearSelection: () => set({ selectedAgents: [] }),
}))
