import { useState, useEffect, useCallback, useRef } from 'react'
import { api } from '../api/client'

/**
 * Fetches and polls balance every `intervalMs` milliseconds.
 */
export function useBalance(merchantId, intervalMs = 5000) {
  const [balance, setBalance] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    if (!merchantId) return
    try {
      const res = await api.getBalance(merchantId)
      setBalance(res.data)
      setError(null)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [merchantId])

  useEffect(() => {
    fetch()
    const id = setInterval(fetch, intervalMs)
    return () => clearInterval(id)
  }, [fetch, intervalMs])

  return { balance, loading, error, refetch: fetch }
}

/**
 * Fetches and polls payout list every `intervalMs` milliseconds.
 */
export function usePayouts(merchantId, intervalMs = 5000) {
  const [payouts, setPayouts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetch = useCallback(async () => {
    if (!merchantId) return
    try {
      const res = await api.getPayouts(merchantId)
      setPayouts(res.data || [])
      setError(null)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [merchantId])

  useEffect(() => {
    fetch()
    const id = setInterval(fetch, intervalMs)
    return () => clearInterval(id)
  }, [fetch, intervalMs])

  return { payouts, loading, error, refetch: fetch }
}

/**
 * Fetches paginated ledger entries.
 */
export function useLedger(merchantId, page = 1) {
  const [entries, setEntries] = useState([])
  const [pagination, setPagination] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!merchantId) return
    setLoading(true)
    api.getLedger(merchantId, page)
      .then((res) => {
        setEntries(res.data || [])
        setPagination(res.pagination)
        setError(null)
      })
      .catch(setError)
      .finally(() => setLoading(false))
  }, [merchantId, page])

  return { entries, pagination, loading, error }
}
