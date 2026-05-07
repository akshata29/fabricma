export const SSE_EVENTS = {
  PLAN: 'plan',
  TOKEN: 'token',
  HITL: 'hitl',
  DONE: 'done',
  ERROR: 'error',
  STATUS: 'status',
} as const

export type SseEventType = typeof SSE_EVENTS[keyof typeof SSE_EVENTS]
