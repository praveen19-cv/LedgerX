import { useBalance } from '../hooks/useData'

function formatINR(paise) {
  if (paise == null) return '—'
  const rupees = paise / 100
  return new Intl.NumberFormat('en-IN', {
    style: 'currency', currency: 'INR', minimumFractionDigits: 2
  }).format(rupees)
}

export default function BalanceCards({ merchantId }) {
  const { balance, loading } = useBalance(merchantId)

  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {[0, 1].map(i => (
          <div key={i} className="stat-card shimmer h-32" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {/* Available Balance */}
      <div className="stat-card relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-brand-600/10 blur-2xl -translate-y-8 translate-x-8" />
        <span className="stat-label">Available Balance</span>
        <span className="stat-value text-brand-400">
          {formatINR(balance?.available_paise)}
        </span>
        <span className="text-xs text-white/40 font-mono">
          {balance?.available_paise?.toLocaleString('en-IN')} paise
        </span>
        <div className="flex items-center gap-1.5 mt-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
          </span>
          <span className="text-xs text-emerald-400/70 font-medium">Live</span>
        </div>
      </div>

      {/* Held Balance */}
      <div className="stat-card relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 rounded-full bg-amber-500/10 blur-2xl -translate-y-8 translate-x-8" />
        <span className="stat-label">On Hold</span>
        <span className="stat-value text-amber-400">
          {formatINR(balance?.held_paise)}
        </span>
        <span className="text-xs text-white/40 font-mono">
          {balance?.held_paise?.toLocaleString('en-IN')} paise
        </span>
        <p className="text-xs text-white/30 mt-2">Reserved for pending payouts</p>
      </div>
    </div>
  )
}
