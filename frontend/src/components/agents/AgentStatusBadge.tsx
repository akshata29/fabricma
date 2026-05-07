import { FileText, Package, TrendingUp, Network } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { AgentInfo } from '@/types/agent'

const AGENT_ICONS: Record<string, React.ElementType> = {
  invoice: FileText,
  inventory: Package,
  sales: TrendingUp,
  orchestrator: Network,
}

interface Props {
  agent: AgentInfo
  selected?: boolean
}

export function AgentStatusBadge({ agent, selected }: Props) {
  const shortName = agent.name.replace('meridian-', '').replace('-agent', '')
  const Icon = AGENT_ICONS[shortName] ?? Network

  const dotColor =
    agent.status === 'available'
      ? 'bg-emerald-500'
      : agent.status === 'busy'
        ? 'bg-amber-500'
        : 'bg-zinc-500'

  return (
    <div className={cn('flex items-center gap-2.5 w-full', selected && 'font-semibold')}>
      <div className={cn(
        'flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg transition-colors',
        selected ? 'bg-primary/15 text-primary' : 'bg-muted text-muted-foreground',
      )}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="flex flex-col min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <span className="text-sm text-foreground truncate capitalize">{shortName}</span>
          <span className={cn('h-1.5 w-1.5 rounded-full flex-shrink-0', dotColor)} />
        </div>
        <span className="text-xs text-muted-foreground truncate">
          {agent.description.split('—')[0].trim()}
        </span>
      </div>
    </div>
  )
}
