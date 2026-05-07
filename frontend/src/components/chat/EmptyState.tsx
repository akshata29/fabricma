import { Bot, FileText, Package, TrendingUp, BarChart3, ArrowRightLeft, Network, Layers } from 'lucide-react'
import { useChatStore } from '@/store/chatStore'
import { useChatStream } from '@/hooks/useChatStream'
import { useSession } from '@/hooks/useSession'

const SUGGESTIONS = [
  {
    icon: FileText,
    category: 'Invoice',
    label: 'Unpaid invoices from 2024',
    query: 'How many invoices are still unpaid from 2024, and what is their combined value?',
  },
  {
    icon: Package,
    category: 'Inventory',
    label: 'Products below reorder threshold',
    query: 'Which products are below their reorder threshold based on current stock levels?',
  },
  {
    icon: TrendingUp,
    category: 'Sales',
    label: 'Top 3 sales reps by revenue in 2024',
    query: 'Who are the top 3 sales reps by total revenue in 2024?',
  },
  {
    icon: BarChart3,
    category: 'Parallel',
    label: '2024 business summary across all domains',
    query:
      'Give me a business summary for 2024: total outstanding AR invoice value, products below reorder threshold, and the top 3 territories by sales revenue.',
  },
  {
    icon: ArrowRightLeft,
    category: 'Sequential',
    label: 'Top products by sales → stockout risk',
    query:
      'List the top 10 products by sales revenue in 2024, then show their current stock levels — which are at risk of a stockout?',
  },
  {
    icon: Network,
    category: 'Full fan-out',
    label: 'Complete picture for Heavy-Duty Lighting 10-Pack',
    query:
      'Give me a complete picture of our Heavy-Duty Lighting 10-Pack — its sales history in 2024, current stock across all warehouses, and any outstanding supplier invoices.',
  },
  {
    icon: Layers,
    category: 'Parallel',
    label: 'Strong sellers running low on stock',
    query: 'Which products had strong sales in 2024 but are currently running low on inventory?',
  },
  {
    icon: FileText,
    category: 'Sequential',
    label: 'Customers with overdue invoices still buying?',
    query:
      'Find all customers with overdue unpaid AR invoices, then show me their total sales in 2024 — are they still buying despite unpaid invoices?',
  },
]

export function EmptyState() {
  const { addMessage } = useChatStore()
  const { sendMessage } = useChatStream()
  const { sessionId } = useSession()

  const handleSuggestion = async (query: string) => {
    if (!sessionId) return
    addMessage({
      id: crypto.randomUUID(),
      role: 'user',
      content: query,
      timestamp: new Date(),
    })
    await sendMessage(query, sessionId)
  }

  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-8 px-6">
      <div className="text-center">
        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 ring-1 ring-primary/20">
          <Bot className="h-7 w-7 text-primary" />
        </div>
        <h2 className="text-xl font-semibold text-foreground">Meridian Analytics</h2>
        <p className="mt-1.5 text-sm text-muted-foreground max-w-xs mx-auto">
          Ask anything about invoices, inventory, or sales data
        </p>
      </div>
      <div className="grid grid-cols-1 gap-2 w-full max-w-2xl sm:grid-cols-2">
        {SUGGESTIONS.map(({ icon: Icon, category, label, query }) => (
          <button
            key={label}
            onClick={() => handleSuggestion(query)}
            className="group flex items-start gap-3 rounded-xl border border-border bg-card p-3.5 text-left transition-all hover:border-primary/40 hover:bg-accent"
          >
            <Icon className="h-4 w-4 mt-0.5 flex-shrink-0 text-muted-foreground transition-colors group-hover:text-primary" />
            <div className="flex flex-col gap-0.5 min-w-0">
              <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground/60">
                {category}
              </span>
              <span className="text-xs text-muted-foreground leading-relaxed transition-colors group-hover:text-foreground">
                {label}
              </span>
            </div>
          </button>
        ))}
      </div>
    </div>
  )
}
