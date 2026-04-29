import { usePayouts } from '../hooks/useData'
import { formatDistanceToNow } from 'date-fns'

function StatusBadge({ status }) {
  const map = {
    PENDING: 'badge-pending',
    PROCESSING: 'badge-processing',
    COMPLETED: 'badge-completed',
    FAILED: 'badge-failed',
  }
  const icons = {
    PENDING: '⏳',
    PROCESSING: '⚡',
    COMPLETED: '✓',
    FAILED: '✕',
  }
  return (
    <span className={map[status] || 'badge bg-white/10 text-white/60'}>
      {icons[status]} {status}
    </span>
  )
}

function formatINR(paise) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', minimumFractionDigits: 2
  }).format(paise / 100)
}

export default function PayoutTable({ merchantId }) {
  const { payouts, loading } = usePayouts(merchantId)

  if (loading) {
    return (
      <div className="glass-card p-6 space-y-3">
        {[0, 1, 2].map(i => (
          <div key={i} className="shimmer h-14 rounded-lg" />
        ))}
      </div>
    )
  }

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-6 py-4 border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-brand-600/20 flex items-center justify-center">
            <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <h2 className="text-base font-semibold text-white">Payout History</h2>
        </div>
        <span className="text-xs text-white/30">Auto-refreshes every 5s</span>
      </div>

      {payouts.length === 0 ? (
        <div className="p-12 text-center text-white/30">
          <svg className="w-12 h-12 mx-auto mb-3 opacity-30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          No payouts yet
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">ID</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Amount</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Status</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Retries</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {payouts.map((p) => (
                <tr key={p.id} className="hover:bg-white/3 transition-colors duration-150 group">
                  <td className="px-6 py-4">
                    <span className="font-mono text-xs text-white/40 group-hover:text-white/60 transition-colors">
                      {p.id.slice(0, 8)}…
                    </span>
                  </td>
                  <td className="px-6 py-4 font-semibold text-white tabular-nums">
                    {formatINR(p.amount_paise)}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={p.status} />
                    {p.failure_reason && (
                      <p className="text-xs text-red-400/70 mt-1 truncate max-w-xs">{p.failure_reason}</p>
                    )}
                  </td>
                  <td className="px-6 py-4 text-white/40 tabular-nums">{p.retry_count}</td>
                  <td className="px-6 py-4 text-white/40 text-xs">
                    {formatDistanceToNow(new Date(p.created_at), { addSuffix: true })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
