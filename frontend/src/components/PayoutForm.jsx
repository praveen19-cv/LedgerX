import { useState } from 'react'
import { v4 as uuidv4 } from 'uuid'
import toast from 'react-hot-toast'
import { api } from '../api/client'

export default function PayoutForm({ merchant, onSuccess }) {
  const [amountRupees, setAmountRupees] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const bankAccount = merchant?.bank_accounts?.[0]

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!bankAccount) {
      toast.error('No bank account found for this merchant.')
      return
    }

    const amount = parseFloat(amountRupees)
    if (isNaN(amount) || amount <= 0) {
      toast.error('Enter a valid amount greater than ₹0')
      return
    }

    const amountPaise = Math.round(amount * 100)
    const idempotencyKey = uuidv4()

    setSubmitting(true)
    try {
      await api.createPayout(
        {
          merchant_id: merchant.id,
          bank_account_id: bankAccount.id,
          amount_paise: amountPaise,
        },
        idempotencyKey
      )
      toast.success('Payout request submitted!')
      setAmountRupees('')
      onSuccess?.()
    } catch (err) {
      const msg =
        err?.data?.error ||
        (typeof err?.data?.error === 'object' ? JSON.stringify(err.data.error) : 'Request failed')
      toast.error(msg)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="glass-card p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-brand-600/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-semibold text-white">Request Payout</h2>
          <p className="text-xs text-white/40">Funds will be held pending settlement</p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-white/60 mb-1.5">
            Amount (₹)
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-white/40 font-semibold">₹</span>
            <input
              id="payout-amount"
              type="number"
              min="0.01"
              step="0.01"
              value={amountRupees}
              onChange={(e) => setAmountRupees(e.target.value)}
              placeholder="0.00"
              className="input-field pl-8"
              required
            />
          </div>
          {amountRupees && (
            <p className="text-xs text-white/30 mt-1 font-mono">
              = {Math.round(parseFloat(amountRupees) * 100).toLocaleString('en-IN')} paise
            </p>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-white/60 mb-1.5">
            Bank Account
          </label>
          {bankAccount ? (
            <div className="bg-surface-600/50 border border-white/5 rounded-xl px-4 py-3 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-600/20 flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <div>
                <p className="text-sm font-medium text-white">{bankAccount.account_holder_name}</p>
                <p className="text-xs text-white/40 font-mono">••••{bankAccount.account_number.slice(-4)} · {bankAccount.ifsc_code}</p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-red-400">No bank account linked</p>
          )}
        </div>

        <button
          id="submit-payout-btn"
          type="submit"
          disabled={submitting || !bankAccount}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing…
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Submit Payout Request
            </>
          )}
        </button>
      </form>
    </div>
  )
}
