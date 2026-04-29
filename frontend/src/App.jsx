import { useState, useEffect } from 'react'
import toast from 'react-hot-toast'
import { api } from './api/client'
import BalanceCards from './components/BalanceCards'
import PayoutForm from './components/PayoutForm'
import PayoutTable from './components/PayoutTable'
import LedgerTable from './components/LedgerTable'

const TABS = ['Overview', 'Ledger']

export default function App() {
  const [merchants, setMerchants] = useState([])
  const [selectedMerchant, setSelectedMerchant] = useState(null)
  const [activeTab, setActiveTab] = useState('Overview')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    api.getMerchants()
      .then(res => {
        setMerchants(res.data || [])
        if (res.data?.length > 0) setSelectedMerchant(res.data[0])
      })
      .catch(() => toast.error('Failed to load merchants'))
  }, [])

  function handlePayoutSuccess() {
    setRefreshKey(k => k + 1)
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-white/5 sticky top-0 z-50 backdrop-blur-xl bg-surface-900/70">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center shadow-lg shadow-brand-600/30">
              <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <span className="text-xl font-bold tracking-tight">
              Ledger<span className="text-brand-400">X</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            {/* Merchant selector */}
            {merchants.length > 0 && (
              <select
                id="merchant-selector"
                value={selectedMerchant?.id || ''}
                onChange={e => {
                  const m = merchants.find(m => m.id === e.target.value)
                  setSelectedMerchant(m)
                }}
                className="bg-surface-700 border border-white/10 text-white text-sm rounded-lg px-3 py-2 
                           focus:outline-none focus:ring-2 focus:ring-brand-500/50 cursor-pointer"
              >
                {merchants.map(m => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            )}

            <div className="flex items-center gap-1.5 bg-surface-700/50 border border-white/5 rounded-full px-3 py-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="text-xs text-emerald-400/80 font-medium">Engine Online</span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!selectedMerchant ? (
          <div className="flex items-center justify-center h-64 text-white/30">
            <div className="text-center">
              <div className="w-16 h-16 rounded-2xl bg-surface-700/50 flex items-center justify-center mx-auto mb-4 shimmer" />
              <p>Loading merchants…</p>
            </div>
          </div>
        ) : (
          <>
            {/* Merchant greeting */}
            <div className="mb-8">
              <h1 className="text-2xl font-bold text-white">
                {selectedMerchant.name}
                <span className="text-white/30 font-normal text-xl ml-2">— Payout Dashboard</span>
              </h1>
              <p className="text-sm text-white/40 mt-1 font-mono">{selectedMerchant.id}</p>
            </div>

            {/* Tab navigation */}
            <div className="flex gap-1 mb-6 bg-surface-800/60 rounded-xl p-1 w-fit border border-white/5">
              {TABS.map(tab => (
                <button
                  key={tab}
                  id={`tab-${tab.toLowerCase()}`}
                  onClick={() => setActiveTab(tab)}
                  className={`px-5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === tab
                      ? 'bg-brand-600 text-white shadow-lg shadow-brand-600/20'
                      : 'text-white/50 hover:text-white/80'
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {activeTab === 'Overview' && (
              <div className="space-y-6">
                <BalanceCards key={refreshKey} merchantId={selectedMerchant.id} />
                <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
                  <div className="lg:col-span-2">
                    <PayoutForm
                      merchant={selectedMerchant}
                      onSuccess={handlePayoutSuccess}
                    />
                  </div>
                  <div className="lg:col-span-3">
                    <PayoutTable key={refreshKey} merchantId={selectedMerchant.id} />
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'Ledger' && (
              <LedgerTable key={refreshKey} merchantId={selectedMerchant.id} />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 mt-16 py-6">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between text-xs text-white/20">
          <span>LedgerX Payout Engine · ACID · Idempotent · Concurrent-Safe</span>
          <span>PostgreSQL · Celery · Redis</span>
        </div>
      </footer>
    </div>
  )
}
