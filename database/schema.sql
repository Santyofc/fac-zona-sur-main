-- ============================================================
-- Factura CR — PostgreSQL Schema
-- Compatible con Supabase (habilita uuid-ossp y pgcrypto)
-- ============================================================

-- Extensiones requeridas
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ────────────────────────────────────────────────────────────
-- TABLA: companies
-- Empresa emisora de facturas (tenant)
-- ────────────────────────────────────────────────────────────
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Identificación
    name            VARCHAR(255) NOT NULL,
    trade_name      VARCHAR(255),                           -- Nombre comercial
    cedula_type     VARCHAR(10) NOT NULL DEFAULT 'FISICA',  -- FISICA, JURIDICA, DIMEX, NITE
    cedula_number   VARCHAR(20) NOT NULL UNIQUE,

    -- Contacto
    email           VARCHAR(255) NOT NULL UNIQUE,
    phone           VARCHAR(30),
    website         VARCHAR(255),

    -- Dirección
    province        VARCHAR(100),
    canton          VARCHAR(100),
    district        VARCHAR(100),
    address         TEXT,

    -- Configuración Hacienda
    hacienda_user   VARCHAR(255),
    hacienda_pass_encrypted TEXT,                          -- AES-256 encrypted
    cert_path       VARCHAR(500),
    cert_pin_encrypted TEXT,

    -- Configuración factura
    invoice_prefix  VARCHAR(10) DEFAULT 'E-',
    consecutive_num BIGINT NOT NULL DEFAULT 1,
    economic_activity VARCHAR(10),                         -- Código actividad económica BCCR
    
    -- Suscripción SaaS
    plan            VARCHAR(20) NOT NULL DEFAULT 'free',   -- free, starter, pro, enterprise
    plan_expires_at TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    
    CONSTRAINT chk_cedula_type CHECK (cedula_type IN ('FISICA', 'JURIDICA', 'DIMEX', 'NITE'))
);

-- ────────────────────────────────────────────────────────────
-- TABLA: users
-- Usuarios vinculados a una empresa
-- ────────────────────────────────────────────────────────────
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Datos del usuario
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT,                                  -- NULL si usa OAuth/Supabase Auth
    full_name       VARCHAR(255) NOT NULL,
    avatar_url      VARCHAR(500),
    
    -- Rol y permisos
    role            VARCHAR(20) NOT NULL DEFAULT 'viewer', -- owner, admin, accountant, viewer
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    
    CONSTRAINT chk_role CHECK (role IN ('owner', 'admin', 'accountant', 'viewer'))
);

-- ────────────────────────────────────────────────────────────
-- TABLA: clients
-- Receptores de facturas
-- ────────────────────────────────────────────────────────────
CREATE TABLE clients (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Identificación
    name            VARCHAR(255) NOT NULL,
    cedula_type     VARCHAR(10) NOT NULL DEFAULT 'FISICA',
    cedula_number   VARCHAR(20),
    
    -- Contacto
    email           VARCHAR(255),
    phone           VARCHAR(30),
    
    -- Dirección
    province        VARCHAR(100),
    canton          VARCHAR(100),
    district        VARCHAR(100),
    address         TEXT,
    
    -- Metadatos
    notes           TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    
    CONSTRAINT chk_client_cedula_type CHECK (cedula_type IN ('FISICA', 'JURIDICA', 'DIMEX', 'NITE', 'EXTRANJERO'))
);

-- ────────────────────────────────────────────────────────────
-- TABLA: products
-- Productos/servicios que se facturan
-- ────────────────────────────────────────────────────────────
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    -- Identificación
    code            VARCHAR(50),                           -- Código interno
    cabys_code      VARCHAR(20),                           -- Código CABYS Hacienda
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    
    -- Precio y taxes
    unit_price      NUMERIC(12, 5) NOT NULL DEFAULT 0,
    currency        VARCHAR(3) NOT NULL DEFAULT 'CRC',     -- CRC, USD
    tax_rate        NUMERIC(5, 2) NOT NULL DEFAULT 13.0,   -- IVA: 0, 1, 2, 4, 8, 13
    unit_measure    VARCHAR(20) NOT NULL DEFAULT 'Sp',     -- Sp=Servicio, Unid=Unidad, etc.
    
    is_active       BOOLEAN NOT NULL DEFAULT TRUE
);

-- ────────────────────────────────────────────────────────────
-- TABLA: invoices
-- Facturas electrónicas emitidas
-- ────────────────────────────────────────────────────────────
CREATE TABLE invoices (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    client_id       UUID REFERENCES clients(id) ON DELETE SET NULL,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Numeración Hacienda
    consecutive     VARCHAR(20) NOT NULL,                  -- 00100001010000000001
    clave           VARCHAR(50) UNIQUE,                    -- Clave 50 dígitos Hacienda
    
    -- Tipo de documento
    doc_type        VARCHAR(5) NOT NULL DEFAULT 'FE',      -- FE=Factura, TE=Tiquete, NC=Nota Crédito, ND=Nota Débito
    
    -- Fechas
    issue_date      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    due_date        TIMESTAMPTZ,
    
    -- Montos
    currency        VARCHAR(3) NOT NULL DEFAULT 'CRC',
    exchange_rate   NUMERIC(12, 5) DEFAULT 1.0,
    subtotal        NUMERIC(12, 5) NOT NULL DEFAULT 0,
    tax_total       NUMERIC(12, 5) NOT NULL DEFAULT 0,
    discount_total  NUMERIC(12, 5) NOT NULL DEFAULT 0,
    total           NUMERIC(12, 5) NOT NULL DEFAULT 0,
    
    -- Condición de venta
    sale_condition  VARCHAR(5) NOT NULL DEFAULT '01',      -- 01=Contado, 02=Crédito, etc.
    payment_method  VARCHAR(5) NOT NULL DEFAULT '01',      -- 01=Efectivo, 02=Tarjeta, etc.
    credit_term_days INT DEFAULT 0,
    
    -- Estado
    status          VARCHAR(20) NOT NULL DEFAULT 'draft',
    -- draft | processing | sent | accepted | rejected | cancelled
    
    -- Notas
    notes           TEXT,
    
    CONSTRAINT chk_doc_type CHECK (doc_type IN ('FE', 'TE', 'NC', 'ND', 'CCE', 'CPCE')),
    CONSTRAINT chk_status CHECK (status IN ('draft', 'processing', 'sent', 'accepted', 'rejected', 'cancelled'))
);

-- ────────────────────────────────────────────────────────────
-- TABLA: invoice_items
-- Líneas de detalle de cada factura
-- ────────────────────────────────────────────────────────────
CREATE TABLE invoice_items (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    invoice_id      UUID NOT NULL REFERENCES invoices(id) ON DELETE CASCADE,
    product_id      UUID REFERENCES products(id) ON DELETE SET NULL,

    -- Detalle de línea
    line_number     SMALLINT NOT NULL,
    cabys_code      VARCHAR(20),
    description     VARCHAR(500) NOT NULL,
    unit_measure    VARCHAR(20) NOT NULL DEFAULT 'Sp',
    quantity        NUMERIC(12, 5) NOT NULL DEFAULT 1,
    unit_price      NUMERIC(12, 5) NOT NULL,
    discount_pct    NUMERIC(5, 2) DEFAULT 0,
    discount_amount NUMERIC(12, 5) DEFAULT 0,
    subtotal        NUMERIC(12, 5) NOT NULL,
    tax_rate        NUMERIC(5, 2) NOT NULL DEFAULT 13.0,
    tax_amount      NUMERIC(12, 5) NOT NULL,
    total           NUMERIC(12, 5) NOT NULL
);

-- ────────────────────────────────────────────────────────────
-- TABLA: hacienda_documents
-- Registro de intercambios con la API de Hacienda
-- ────────────────────────────────────────────────────────────
CREATE TABLE hacienda_documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    invoice_id      UUID NOT NULL UNIQUE REFERENCES invoices(id) ON DELETE CASCADE,

    -- XML generado
    xml_content     TEXT,                                  -- XML sin firmar
    xml_signed      TEXT,                                  -- XML firmado
    xml_filename    VARCHAR(255),

    -- Respuesta de Hacienda
    submission_date TIMESTAMPTZ,
    hacienda_status VARCHAR(20),                           -- procesando | aceptado | rechazado
    hacienda_msg    TEXT,
    hacienda_detail TEXT,
    
    -- Acuse de recibo XML (MH)
    response_xml    TEXT,
    response_date   TIMESTAMPTZ,
    
    -- PDF generado
    pdf_url         VARCHAR(500),
    pdf_generated_at TIMESTAMPTZ,
    
    -- Intentos de envío
    send_attempts   SMALLINT NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMPTZ,
    
    CONSTRAINT chk_hacienda_status CHECK (hacienda_status IN ('procesando', 'aceptado', 'rechazado', NULL))
);

-- ────────────────────────────────────────────────────────────
-- TABLA: payments
-- Historial de pagos de suscripciones (PayPal / SINPE)
-- ────────────────────────────────────────────────────────────
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    company_id      UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    
    -- Detalles del Pago
    amount          NUMERIC(12, 2) NOT NULL,
    currency        VARCHAR(3) NOT NULL DEFAULT 'USD',     -- USD para PayPal, CRC para SINPE
    payment_method  VARCHAR(20) NOT NULL,                  -- 'paypal' o 'manual' (SINPE)
    
    -- Referencias externas
    reference_id    VARCHAR(255),                          -- PayPal Order ID o Número de Comprobante SINPE
    receipt_url     VARCHAR(500),                          -- URL de la imagen del comprobante (para pagos manuales)
    
    -- Estado
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    
    -- Meses adquiridos (para el cálculo del plan_expires_at)
    months_added    INTEGER NOT NULL DEFAULT 1,
    
    -- Aprobación (para flujos manuales)
    approved_at     TIMESTAMPTZ,
    approved_by     UUID REFERENCES users(id) ON DELETE SET NULL, -- Admin que aprobó
    notes           TEXT,

    CONSTRAINT chk_payment_method CHECK (payment_method IN ('paypal', 'manual')),
    CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'approved', 'rejected'))
);

-- ============================================================
-- ÍNDICES DE PERFORMANCE
-- ============================================================
CREATE INDEX idx_users_company ON users(company_id);
CREATE INDEX idx_clients_company ON clients(company_id);
CREATE INDEX idx_products_company ON products(company_id);
CREATE INDEX idx_invoices_company ON invoices(company_id);
CREATE INDEX idx_invoices_client ON invoices(client_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_issue_date ON invoices(issue_date DESC);
CREATE INDEX idx_invoice_items_invoice ON invoice_items(invoice_id);
CREATE INDEX idx_hacienda_docs_invoice ON hacienda_documents(invoice_id);
CREATE INDEX idx_payments_company ON payments(company_id);

-- ============================================================
-- TRIGGERS: updated_at automático
-- ============================================================
CREATE OR REPLACE FUNCTION trigger_set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at_companies BEFORE UPDATE ON companies FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER set_updated_at_users BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER set_updated_at_clients BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER set_updated_at_products BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER set_updated_at_invoices BEFORE UPDATE ON invoices FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER set_updated_at_invoice_items BEFORE UPDATE ON invoice_items FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER set_updated_at_hacienda_documents BEFORE UPDATE ON hacienda_documents FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();
CREATE TRIGGER set_updated_at_payments BEFORE UPDATE ON payments FOR EACH ROW EXECUTE FUNCTION trigger_set_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY (Supabase Multi-tenant)
-- ============================================================
ALTER TABLE companies       ENABLE ROW LEVEL SECURITY;
ALTER TABLE users           ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients         ENABLE ROW LEVEL SECURITY;
ALTER TABLE products        ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices        ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_items   ENABLE ROW LEVEL SECURITY;
ALTER TABLE hacienda_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments        ENABLE ROW LEVEL SECURITY;

-- Los usuarios solo ven los datos de SU empresa
-- Se asume que auth.jwt() → company_id está en el claim personalizado
CREATE POLICY "users_own_company" ON users
    USING (company_id = (auth.jwt() ->> 'company_id')::UUID);

CREATE POLICY "clients_own_company" ON clients
    USING (company_id = (auth.jwt() ->> 'company_id')::UUID);

CREATE POLICY "products_own_company" ON products
    USING (company_id = (auth.jwt() ->> 'company_id')::UUID);

CREATE POLICY "invoices_own_company" ON invoices
    USING (company_id = (auth.jwt() ->> 'company_id')::UUID);

CREATE POLICY "invoice_items_via_invoice" ON invoice_items
    USING (invoice_id IN (
        SELECT id FROM invoices WHERE company_id = (auth.jwt() ->> 'company_id')::UUID
    ));

CREATE POLICY "hacienda_docs_via_invoice" ON hacienda_documents
    USING (invoice_id IN (
        SELECT id FROM invoices WHERE company_id = (auth.jwt() ->> 'company_id')::UUID
    ));

CREATE POLICY "payments_own_company" ON payments
    USING (company_id = (auth.jwt() ->> 'company_id')::UUID);
