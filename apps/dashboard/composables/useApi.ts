/**
 * useClients — Composable para gestión de clientes
 */
export function useClients() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const getHeaders = () => {
    const token = localStorage.getItem('fcr_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async function fetchClients(params?: { search?: string }) {
    const query: Record<string, string> = {}
    if (params?.search) query.search = params.search
    return await $fetch('/clients', { baseURL: apiBase, headers: getHeaders(), query }) as any[]
  }

  async function createClient(data: Record<string, unknown>) {
    return await $fetch('/clients', {
      method: 'POST', baseURL: apiBase,
      headers: { ...getHeaders(), 'Content-Type': 'application/json' }, body: data,
    })
  }

  async function updateClient(id: string, data: Record<string, unknown>) {
    return await $fetch(`/clients/${id}`, {
      method: 'PUT', baseURL: apiBase,
      headers: { ...getHeaders(), 'Content-Type': 'application/json' }, body: data,
    })
  }

  async function deleteClient(id: string) {
    return await $fetch(`/clients/${id}`, {
      method: 'DELETE', baseURL: apiBase, headers: getHeaders(),
    })
  }

  return { fetchClients, createClient, updateClient, deleteClient }
}

/**
 * useProducts — Composable para gestión de productos
 */
export function useProducts() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase
  const getHeaders = () => {
    const token = localStorage.getItem('fcr_token')
    return token ? { Authorization: `Bearer ${token}` } : {}
  }

  async function fetchProducts(params?: { search?: string }) {
    const query: Record<string, string> = {}
    if (params?.search) query.search = params.search
    return await $fetch('/products', { baseURL: apiBase, headers: getHeaders(), query }) as any[]
  }

  async function createProduct(data: Record<string, unknown>) {
    return await $fetch('/products', {
      method: 'POST', baseURL: apiBase,
      headers: { ...getHeaders(), 'Content-Type': 'application/json' }, body: data,
    })
  }

  async function updateProduct(id: string, data: Record<string, unknown>) {
    return await $fetch(`/products/${id}`, {
      method: 'PUT', baseURL: apiBase,
      headers: { ...getHeaders(), 'Content-Type': 'application/json' }, body: data,
    })
  }

  return { fetchProducts, createProduct, updateProduct }
}

/**
 * useApi — Composable genérico para auth
 */
export function useApi() {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiBase

  async function login(email: string, password: string) {
    const result = await $fetch('/auth/login', {
      method: 'POST', baseURL: apiBase,
      headers: { 'Content-Type': 'application/json' },
      body: { email, password },
    }) as { access_token: string; user_id: string; company_id: string }
    localStorage.setItem('fcr_token', result.access_token)
    localStorage.setItem('fcr_user_id', result.user_id)
    localStorage.setItem('fcr_company_id', result.company_id)
    return result
  }

  async function register(data: Record<string, unknown>) {
    return await $fetch('/auth/register', {
      method: 'POST', baseURL: apiBase,
      headers: { 'Content-Type': 'application/json' }, body: data,
    })
  }

  function logout() {
    localStorage.removeItem('fcr_token')
    localStorage.removeItem('fcr_user_id')
    localStorage.removeItem('fcr_company_id')
    navigateTo('/auth/login')
  }

  function isAuthenticated() {
    return !!localStorage.getItem('fcr_token')
  }

  return { login, register, logout, isAuthenticated }
}
