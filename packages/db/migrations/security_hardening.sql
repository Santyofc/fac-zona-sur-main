-- Database Hardening: Security (RLS) and Performance (Indexes)
-- Generated for Zona Sur Tech - FacturaCR SaaS

-- 1. Enable Row Level Security (RLS)
ALTER TABLE "public"."companies" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."users" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."clients" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."products" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."invoices" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."invoice_items" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."hacienda_documents" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."payments" ENABLE ROW LEVEL SECURITY;

-- 2. Create Performance Indexes for Foreign Keys
-- These indexes resolve the "Unindexed foreign keys" warnings

-- Users -> Company
CREATE INDEX IF NOT EXISTS "ix_users_company_id" ON "public"."users" ("company_id");

-- Clients -> Company
CREATE INDEX IF NOT EXISTS "ix_clients_company_id" ON "public"."clients" ("company_id");

-- Products -> Company
CREATE INDEX IF NOT EXISTS "ix_products_company_id" ON "public"."products" ("company_id");

-- Invoices -> Company & Client
CREATE INDEX IF NOT EXISTS "ix_invoices_company_id" ON "public"."invoices" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_invoices_client_id" ON "public"."invoices" ("client_id");

-- Invoice Items -> Invoice & Product
CREATE INDEX IF NOT EXISTS "ix_invoice_items_invoice_id" ON "public"."invoice_items" ("invoice_id");
CREATE INDEX IF NOT EXISTS "ix_invoice_items_product_id" ON "public"."invoice_items" ("product_id");

-- Hacienda Documents -> Invoice
CREATE INDEX IF NOT EXISTS "ix_hacienda_documents_invoice_id" ON "public"."hacienda_documents" ("invoice_id");

-- Payments -> Company & ApprovedBy
CREATE INDEX IF NOT EXISTS "ix_payments_company_id" ON "public"."payments" ("company_id");
CREATE INDEX IF NOT EXISTS "ix_payments_approved_by" ON "public"."payments" ("approved_by");

-- 3. Basic Isolation Policies (Placeholders - Requires Supabase Auth)
-- These allow access only to the user's own data based on company_id
-- Note: Replace 'current_setting('app.current_company_id')' with your actual tenant identifier logic if not using default Supabase auth mapping.

-- Example for 'invoices':
-- CREATE POLICY "Users can view their own company invoices" ON "public"."invoices"
-- FOR SELECT USING (company_id::text = current_setting('app.current_company_id', true));
