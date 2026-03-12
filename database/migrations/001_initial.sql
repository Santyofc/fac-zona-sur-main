-- Migration 001: Initial schema
-- Created: 2026-03-11
-- Aplica el esquema completo de factura-cr

-- Referencia schema.sql completo
\i ../schema.sql

-- Datos semilla de desarrollo
INSERT INTO companies (id, name, trade_name, cedula_type, cedula_number, email, phone, province, canton, district, address, plan)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'Demo Empresa S.A.',
    'Demo CR',
    'JURIDICA',
    '3-101-999999',
    'demo@empresa.cr',
    '+506 2222-3333',
    'San José',
    'San José',
    'Carmen',
    'De la Caja Costarricense de Seguro Social, 100m Norte',
    'starter'
);

INSERT INTO users (company_id, email, full_name, role)
VALUES (
    'a0000000-0000-0000-0000-000000000001',
    'admin@empresa.cr',
    'Admin Demo',
    'owner'
);
