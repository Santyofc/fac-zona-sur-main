/**
 * useInvoices — Composable para operaciones de facturación
 */
export function useInvoices() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  const getHeaders = () => {
    const token = localStorage.getItem('fcr_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async function fetchStats() {
    const data = await $fetch('/invoices/stats', {
      baseURL: apiBase,
      headers: getHeaders(),
    })
    return data
  }

  async function fetchInvoices(params?: { limit?: number; skip?: number; status?: string }) {
    const query: Record<string, string | number> = {}
    if (params?.limit) query.limit = params.limit
    if (params?.skip) query.skip = params.skip
    if (params?.status) query.status = params.status

    const data = await $fetch('/invoices', {
      baseURL: apiBase,
      headers: getHeaders(),
      query,
    })
    return data as any[]
  }

  async function getInvoice(id: string) {
    return await $fetch(`/invoices/${id}`, {
      baseURL: apiBase,
      headers: getHeaders(),
    })
  }

  async function createInvoice(payload: Record<string, unknown>) {
    return await $fetch('/invoices', {
      method: 'POST',
      baseURL: apiBase,
      headers: { ...getHeaders(), 'Content-Type': 'application/json' },
      body: payload,
    })
  }

  async function sendInvoice(id: string) {
    return await $fetch(`/invoices/${id}/send`, {
      method: 'POST',
      baseURL: apiBase,
      headers: getHeaders(),
    })
  }

  async function getInvoiceStatus(id: string) {
    return await $fetch(`/invoices/${id}/status`, {
      baseURL: apiBase,
      headers: getHeaders(),
    })
  }

  return {
    fetchStats,
    fetchInvoices,
    getInvoice,
    createInvoice,
    sendInvoice,
    getInvoiceStatus,
  }
}
