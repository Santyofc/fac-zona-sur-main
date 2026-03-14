-- Security Hardening: Multi-tenant RLS Policies
-- Target: Supabase authenticated users

-- 0. Helper function to check company access
-- This avoids repeating the subquery in every policy and handles isolation efficiently
CREATE OR REPLACE FUNCTION public.get_auth_company_ids()
RETURNS SETOF uuid AS $$
  SELECT company_id FROM public.users WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER SET search_path = public;

-- 1. Policies for 'companies'
DROP POLICY IF EXISTS "Users can view their own company" ON public.companies;
CREATE POLICY "Users can view their own company" ON public.companies
FOR SELECT USING (id IN (SELECT public.get_auth_company_ids()));

-- 2. Policies for 'users'
DROP POLICY IF EXISTS "Users can only see themselves" ON public.users;
CREATE POLICY "Users can only see themselves" ON public.users
FOR ALL USING (id = auth.uid());

-- 3. Policies for 'clients'
DROP POLICY IF EXISTS "Users can manage clients of their company" ON public.clients;
CREATE POLICY "Users can manage clients of their company" ON public.clients
FOR ALL USING (company_id IN (SELECT public.get_auth_company_ids()));

-- 4. Policies for 'products'
DROP POLICY IF EXISTS "Users can manage products of their company" ON public.products;
CREATE POLICY "Users can manage products of their company" ON public.products
FOR ALL USING (company_id IN (SELECT public.get_auth_company_ids()));

-- 5. Policies for 'invoices'
DROP POLICY IF EXISTS "Users can manage invoices of their company" ON public.invoices;
CREATE POLICY "Users can manage invoices of their company" ON public.invoices
FOR ALL USING (company_id IN (SELECT public.get_auth_company_ids()));

-- 6. Policies for 'invoice_items'
DROP POLICY IF EXISTS "Users can manage items of their company invoices" ON public.invoice_items;
CREATE POLICY "Users can manage items of their company invoices" ON public.invoice_items
FOR ALL USING (
  invoice_id IN (
    SELECT i.id FROM public.invoices i 
    WHERE i.company_id IN (SELECT public.get_auth_company_ids())
  )
);

-- 7. Policies for 'hacienda_documents'
DROP POLICY IF EXISTS "Users can manage hacienda_documents of their company invoices" ON public.hacienda_documents;
DROP POLICY IF EXISTS "Users can manage hacienda documents of their company invoices" ON public.hacienda_documents;
CREATE POLICY "Users can manage hacienda_documents of their company invoices" ON public.hacienda_documents
FOR ALL USING (
  invoice_id IN (
    SELECT i.id FROM public.invoices i 
    WHERE i.company_id IN (SELECT public.get_auth_company_ids())
  )
);

-- 8. Policies for 'payments'
DROP POLICY IF EXISTS "Users can see payments of their company" ON public.payments;
CREATE POLICY "Users can see payments of their company" ON public.payments
FOR SELECT USING (company_id IN (SELECT public.get_auth_company_ids()));
