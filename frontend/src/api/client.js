const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })
  const data = await res.json()
  if (!res.ok) {
    throw { status: res.status, data }
  }
  return data
}

export const api = {
  getMerchants: () => request('/merchants/'),

  getBalance: (merchantId) =>
    request(`/merchants/${merchantId}/balance/`),

  getLedger: (merchantId, page = 1, pageSize = 20) =>
    request(`/merchants/${merchantId}/ledger/?page=${page}&page_size=${pageSize}`),

  getPayouts: (merchantId) =>
    request(`/payouts/?merchant_id=${merchantId}`),

  createPayout: (body, idempotencyKey) =>
    request('/payouts/', {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify(body),
    }),

  getPayoutById: (payoutId) =>
    request(`/payouts/${payoutId}/`),
}
