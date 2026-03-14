export interface DashboardStats {
  revenue_month: number
  invoices_issued: number
  tax_accumulated: number
  invoices_pending: number
  invoices_accepted?: number
  invoices_rejected?: number
}

export interface Invoice {
  id: string
  number: string
  client_name: string
  date: string
  total: number
  status: 'accepted' | 'pending' | 'rejected' | 'processing'
  currency: string
}
