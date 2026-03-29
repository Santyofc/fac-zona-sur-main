from datetime import datetime
from decimal import Decimal

from sqlalchemy import select

from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.db.models.invoice_item_model import InvoiceItemModel


class SQLAlchemyInvoiceRepository:
    def __init__(self, session):
        self.session = session

    async def create_draft(self, payload: dict) -> dict:
        invoice = InvoiceModel(
            tenant_id=payload['tenant_id'],
            created_by=payload['created_by'],
            customer_id=payload.get('customer_id'),
            doc_type=payload['doc_type'],
            status=payload['status'],
            idempotency_key=payload['idempotency_key'],
            currency=payload['currency'],
            issue_date=payload['issue_date'],
            notes=payload.get('notes'),
        )
        self.session.add(invoice)
        await self.session.flush()

        subtotal = Decimal('0')
        tax_total = Decimal('0')
        for idx, item in enumerate(payload['items'], start=1):
            qty = Decimal(str(item['quantity']))
            unit = Decimal(str(item['unit_price']))
            tax_rate = Decimal(str(item.get('tax_rate', 13)))
            discount_pct = Decimal(str(item.get('discount_pct', 0)))
            raw = qty * unit
            discount = (raw * discount_pct) / Decimal('100')
            line_subtotal = raw - discount
            line_tax = (line_subtotal * tax_rate) / Decimal('100')
            line_total = line_subtotal + line_tax

            subtotal += line_subtotal
            tax_total += line_tax

            self.session.add(
                InvoiceItemModel(
                    tenant_id=payload['tenant_id'],
                    invoice_id=invoice.id,
                    line_number=idx,
                    cabys_code=item.get('cabys_code', '0000000000000'),
                    description=item['description'],
                    quantity=qty,
                    unit_price=unit,
                    discount_pct=discount_pct,
                    subtotal=line_subtotal,
                    tax_total=line_tax,
                    total=line_total,
                )
            )

        invoice.subtotal = subtotal
        invoice.tax_total = tax_total
        invoice.total = subtotal + tax_total
        invoice.updated_at = datetime.utcnow()
        await self.session.flush()
        return self._to_dict(invoice)

    async def list_by_tenant(self, tenant_id):
        result = await self.session.execute(select(InvoiceModel).where(InvoiceModel.tenant_id == tenant_id).order_by(InvoiceModel.created_at.desc()))
        return [self._to_dict(i) for i in result.scalars().all()]

    async def get_by_id(self, tenant_id, invoice_id):
        result = await self.session.execute(
            select(InvoiceModel).where(InvoiceModel.tenant_id == tenant_id, InvoiceModel.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        return self._to_dict(invoice) if invoice else None

    async def update_status(self, tenant_id, invoice_id, status):
        result = await self.session.execute(
            select(InvoiceModel).where(InvoiceModel.tenant_id == tenant_id, InvoiceModel.id == invoice_id)
        )
        invoice = result.scalar_one()
        invoice.status = status
        invoice.updated_at = datetime.utcnow()

    async def update_issue_payload(self, tenant_id, invoice_id, payload):
        result = await self.session.execute(
            select(InvoiceModel).where(InvoiceModel.tenant_id == tenant_id, InvoiceModel.id == invoice_id)
        )
        invoice = result.scalar_one()
        if payload.get('consecutive'):
            invoice.consecutive = payload['consecutive']
        if payload.get('clave'):
            invoice.clave = payload['clave']
        if payload.get('status'):
            invoice.status = payload['status']
        invoice.updated_at = datetime.utcnow()

    async def find_by_idempotency_key(self, tenant_id, key):
        result = await self.session.execute(
            select(InvoiceModel).where(InvoiceModel.tenant_id == tenant_id, InvoiceModel.idempotency_key == key)
        )
        invoice = result.scalar_one_or_none()
        return self._to_dict(invoice) if invoice else None

    @staticmethod
    def _to_dict(invoice: InvoiceModel | None) -> dict | None:
        if not invoice:
            return None
        return {
            'id': invoice.id,
            'tenant_id': invoice.tenant_id,
            'customer_id': invoice.customer_id,
            'created_by': invoice.created_by,
            'doc_type': invoice.doc_type,
            'status': invoice.status,
            'idempotency_key': invoice.idempotency_key,
            'consecutive': invoice.consecutive,
            'clave': invoice.clave,
            'currency': invoice.currency,
            'subtotal': invoice.subtotal,
            'tax_total': invoice.tax_total,
            'total': invoice.total,
            'issue_date': invoice.issue_date,
            'notes': invoice.notes,
        }
