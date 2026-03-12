/**
 * Factura CR — Shared TypeScript Types
 * Used across dashboard and other frontend apps
 */

export type CedulaType = 'FISICA' | 'JURIDICA' | 'DIMEX' | 'NITE' | 'EXTRANJERO'
export type DocType = 'FE' | 'TE' | 'NC' | 'ND'
export type InvoiceStatus = 'draft' | 'processing' | 'sent' | 'accepted' | 'rejected' | 'cancelled'
export type UserRole = 'owner' | 'admin' | 'accountant' | 'viewer'
export type SaleCondition = '01' | '02' | '03' | '04' | '05'
export type PaymentMethod = '01' | '02' | '03' | '04' | '05'

export interface Company {
  id: string
  name: string
  trade_name?: string
  cedula_type: CedulaType
  cedula_number: string
  email: string
  phone?: string
  province?: string
  canton?: string
  district?: string
  address?: string
  plan: string
  is_active: boolean
  consecutive_num: number
  created_at: string
  updated_at: string
}

export interface User {
  id: string
  company_id: string
  email: string
  full_name: string
  avatar_url?: string
  role: UserRole
  is_active: boolean
  last_login_at?: string
  created_at: string
}

export interface Client {
  id: string
  company_id: string
  name: string
  cedula_type: CedulaType
  cedula_number?: string
  email?: string
  phone?: string
  province?: string
  canton?: string
  district?: string
  address?: string
  notes?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Product {
  id: string
  company_id: string
  code?: string
  cabys_code?: string
  name: string
  description?: string
  unit_price: number
  currency: string
  tax_rate: number
  unit_measure: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface InvoiceItem {
  id: string
  invoice_id: string
  product_id?: string
  line_number: number
  cabys_code?: string
  description: string
  unit_measure: string
  quantity: number
  unit_price: number
  discount_pct: number
  discount_amount: number
  subtotal: number
  tax_rate: number
  tax_amount: number
  total: number
}

export interface Invoice {
  id: string
  company_id: string
  client_id?: string
  client?: Client
  consecutive: string
  clave?: string
  doc_type: DocType
  issue_date: string
  due_date?: string
  currency: string
  exchange_rate: number
  subtotal: number
  tax_total: number
  discount_total: number
  total: number
  sale_condition: SaleCondition
  payment_method: PaymentMethod
  credit_term_days: number
  status: InvoiceStatus
  notes?: string
  items: InvoiceItem[]
  created_at: string
  updated_at: string
  // For list views
  client_name?: string
}

export interface HaciendaDocument {
  id: string
  invoice_id: string
  xml_filename?: string
  submission_date?: string
  hacienda_status?: 'procesando' | 'aceptado' | 'rechazado'
  hacienda_msg?: string
  response_date?: string
  pdf_url?: string
  send_attempts: number
  last_attempt_at?: string
}

export interface DashboardStats {
  revenue_month: number
  invoices_issued: number
  tax_accumulated: number
  invoices_pending: number
  invoices_accepted: number
  invoices_rejected: number
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user_id: string
  company_id: string
}

// ─── API Payloads ──────────────────────────────────────────────
export interface InvoiceItemCreate {
  product_id?: string
  cabys_code?: string
  description: string
  unit_measure?: string
  quantity: number
  unit_price: number
  discount_pct?: number
  tax_rate?: number
}

export interface InvoiceCreate {
  client_id?: string
  doc_type?: DocType
  issue_date?: string
  currency?: string
  exchange_rate?: number
  sale_condition?: SaleCondition
  payment_method?: PaymentMethod
  credit_term_days?: number
  notes?: string
  items: InvoiceItemCreate[]
}
