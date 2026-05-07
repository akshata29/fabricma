import { submitHitlApproval } from '@/api/chat'
import { useChatStore } from '@/store/chatStore'
import type { HitlData } from '@/types/chat'

interface Props {
  data: HitlData
}

export function ApprovalDialog({ data }: Props) {
  const { setPendingHitl } = useChatStore()

  const handle = async (approved: boolean) => {
    await submitHitlApproval(data.session_id, approved)
    setPendingHitl(null)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
        <h2 className="text-lg font-semibold text-foreground mb-2">Action Required</h2>
        <p className="text-sm text-muted-foreground mb-4">
          The agent has requested human confirmation before proceeding:
        </p>
        <div className="rounded-md bg-muted p-3 mb-4 text-sm text-foreground">
          <strong>Pattern:</strong> {data.plan.pattern}
          <br />
          <strong>Agents:</strong> {data.plan.agents.join(', ')}
          <br />
          <strong>Rationale:</strong> {data.plan.rationale}
        </div>
        <div className="flex justify-end gap-3">
          <button
            onClick={() => handle(false)}
            className="rounded-md border border-border px-4 py-2 text-sm text-foreground hover:bg-accent transition-colors"
          >
            Reject
          </button>
          <button
            onClick={() => handle(true)}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:opacity-90 transition-opacity"
          >
            Approve
          </button>
        </div>
      </div>
    </div>
  )
}
