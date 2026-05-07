import { useState } from 'react'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { OrchestratorPlan } from '@/types/chat'

interface Props {
  plan: OrchestratorPlan
}

const PATTERN_STYLES: Record<string, string> = {
  single: 'bg-blue-500/15 text-blue-400 border-blue-500/20',
  concurrent: 'bg-purple-500/15 text-purple-400 border-purple-500/20',
  sequential: 'bg-amber-500/15 text-amber-400 border-amber-500/20',
  hitl: 'bg-red-500/15 text-red-400 border-red-500/20',
}

export function PlanPreview({ plan }: Props) {
  const [open, setOpen] = useState(false)

  return (
    <div className="mb-3 overflow-hidden rounded-xl border border-border bg-background/50">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-2 px-3 py-2 text-left transition-colors hover:bg-accent/50"
      >
        <span
          className={cn(
            'rounded-md border px-1.5 py-0.5 font-mono text-[10px] font-medium',
            PATTERN_STYLES[plan.pattern] ?? 'border-border bg-muted text-muted-foreground',
          )}
        >
          {plan.pattern.toUpperCase()}
        </span>
        <span className="flex-1 truncate text-xs text-muted-foreground">
          {plan.agents.join(' → ')}
        </span>
        <ChevronDown
          className={cn(
            'h-3 w-3 flex-shrink-0 text-muted-foreground transition-transform',
            open && 'rotate-180',
          )}
        />
      </button>
      {open && (
        <div className="border-t border-border px-3 py-2 text-xs text-muted-foreground">
          {plan.rationale}
        </div>
      )}
    </div>
  )
}
