import { useLedger } from '../hooks/useData'
import { useState } from 'react'
import { formatDistanceToNow } from 'date-fns'

const TYPE_STYLES = {
  CREDIT: 'text-emerald-400',
  DEBIT: 'text-red-400',
  HOLD: 'text-amber-400',
  RELEASE: 'text-blue-400',
}

const TYPE_SIGN = {
  CREDIT: '+',
  RELEASE: '+',
  DEBIT: '−',
  HOLD: '−',
}

function formatINR(paise) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', minimumFractionDigits: 2
  }).format(paise / 100)
}

export default function LedgerTable({ merchantId }) {
  const [page, setPage] = useState(1)
  const { entries, pagination, loading } = useLedger(merchantId, page)

  return (
    <div className="glass-card overflow-hidden">
      <div className="px-6 py-4 border-b border-white/5 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-purple-600/20 flex items-center justify-center">
          <svg className="w-4 h-4 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18M10 6h4M10 18h4" />
          </svg>
        </div>
        <h2 className="text-base font-semibold text-white">Ledger Entries</h2>
        {pagination && (
          <span className="ml-auto text-xs text-white/30">{pagination.total} total entries</span>
        )}
      </div>

      {loading ? (
        <div className="p-6 space-y-3">
          {[0, 1, 2, 3].map(i => (
            <div key={i} className="shimmer h-12 rounded-lg" />
          ))}
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5">
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Type</th>
                <th className="text-right px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Amount</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Description</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Ref ID</th>
                <th className="text-left px-6 py-3 text-xs font-medium text-white/40 uppercase tracking-wider">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {entries.map((e) => (
                <tr key={e.id} className="hover:bg-white/3 transition-colors duration-150">
                  <td className="px-6 py-3">
                    <span className={`font-semibold ${TYPE_STYLES[e.type] || 'text-white'}`}>
                      {e.type}
                    </span>
                  </td>
                  <td className={`px-6 py-3 text-right font-mono font-semibold tabular-nums ${TYPE_STYLES[e.type]}`}>
                    {TYPE_SIGN[e.type]}{formatINR(e.amount_paise)}
                  </td>
                  <td className="px-6 py-3 text-white/50 text-xs max-w-xs truncate">
                    {e.description || '—'}
                  </td>
                  <td className="px-6 py-3">
                    {e.reference_id ? (
                      <span className="font-mono text-xs text-white/30">
                        {e.reference_id.slice(0, 8)}…
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-6 py-3 text-white/40 text-xs">
                    {formatDistanceToNow(new Date(e.created_at), { addSuffix: true })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          {pagination && pagination.total_pages > 1 && (
            <div className="px-6 py-4 border-t border-white/5 flex items-center gap-3 justify-end">
              <button
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1}
                className="btn-ghost text-sm px-3 py-1.5"
              >
                ← Prev
              </button>
              <span className="text-sm text-white/40">
                Page {page} of {pagination.total_pages}
              </span>
              <button
                onClick={() => setPage(p => Math.min(pagination.total_pages, p + 1))}
                disabled={page === pagination.total_pages}
                className="btn-ghost text-sm px-3 py-1.5"
              >
                Next →
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
