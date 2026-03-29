"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_tenants_name', 'tenants', ['name'], unique=True)

    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])

    op.create_table('customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('id_type', sa.String(20), nullable=False),
        sa.Column('id_number', sa.String(32), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'id_type', 'id_number', name='uq_customer_tenant_identification'),
    )

    op.create_table('products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(64), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('cabys_code', sa.String(20), nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 5), nullable=False),
        sa.Column('tax_rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'code', name='uq_product_tenant_code'),
    )

    op.create_table('certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('alias', sa.String(100), nullable=False),
        sa.Column('p12_path', sa.String(500), nullable=False),
        sa.Column('p12_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table('document_sequences',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('branch', sa.Integer(), nullable=False),
        sa.Column('terminal', sa.Integer(), nullable=False),
        sa.Column('doc_type', sa.String(5), nullable=False),
        sa.Column('current_value', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'branch', 'terminal', 'doc_type', name='uq_sequence_scope'),
    )

    op.create_table('invoices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=False),
        sa.Column('doc_type', sa.String(5), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('idempotency_key', sa.String(120), nullable=False),
        sa.Column('consecutive', sa.String(20), nullable=True),
        sa.Column('clave', sa.String(50), nullable=True),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 5), nullable=False),
        sa.Column('tax_total', sa.Numeric(12, 5), nullable=False),
        sa.Column('total', sa.Numeric(12, 5), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('issue_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'idempotency_key', name='uq_invoice_idempotency'),
        sa.UniqueConstraint('tenant_id', 'consecutive', name='uq_invoice_tenant_consecutive'),
        sa.UniqueConstraint('tenant_id', 'clave', name='uq_invoice_tenant_clave'),
    )

    op.create_table('invoice_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('line_number', sa.SmallInteger(), nullable=False),
        sa.Column('cabys_code', sa.String(20), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('quantity', sa.Numeric(12, 5), nullable=False),
        sa.Column('unit_price', sa.Numeric(12, 5), nullable=False),
        sa.Column('discount_pct', sa.Numeric(5, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(12, 5), nullable=False),
        sa.Column('tax_total', sa.Numeric(12, 5), nullable=False),
        sa.Column('total', sa.Numeric(12, 5), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table('invoice_taxes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoice_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(10), nullable=False),
        sa.Column('rate', sa.Numeric(5, 2), nullable=False),
        sa.Column('amount', sa.Numeric(12, 5), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table('document_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('from_status', sa.String(20), nullable=False),
        sa.Column('to_status', sa.String(20), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table('hacienda_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('idempotency_key', sa.String(120), nullable=False),
        sa.Column('xml_unsigned_url', sa.String(500), nullable=False),
        sa.Column('xml_signed_url', sa.String(500), nullable=False),
        sa.Column('pdf_url', sa.String(500), nullable=True),
        sa.Column('hacienda_payload', sa.JSON(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'invoice_id', 'idempotency_key', name='uq_submission_idempotency'),
    )

    op.create_table('email_deliveries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('invoice_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('invoices.id', ondelete='CASCADE'), nullable=False),
        sa.Column('idempotency_key', sa.String(120), nullable=False),
        sa.Column('recipient_email', sa.String(255), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('provider_payload', sa.JSON(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('tenant_id', 'invoice_id', 'idempotency_key', name='uq_email_delivery_idempotency'),
    )

    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('action', sa.String(120), nullable=False),
        sa.Column('target_type', sa.String(80), nullable=False),
        sa.Column('target_id', sa.String(80), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    for table in [
        'audit_logs', 'email_deliveries', 'hacienda_submissions', 'document_events',
        'invoice_taxes', 'invoice_items', 'invoices', 'document_sequences',
        'certificates', 'products', 'customers', 'users', 'tenants'
    ]:
        op.drop_table(table)
