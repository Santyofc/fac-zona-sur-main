from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.domain.common.enums import DocumentStatus


class CreateInvoiceUseCase:
    def __init__(self, uow):
        self.uow = uow

    async def execute(self, data: dict) -> dict:
        async with self.uow as uow:
            existing = await uow.invoice_repository.find_by_idempotency_key(data['tenant_id'], data['idempotency_key'])
            if existing:
                return existing
            payload = {
                'tenant_id': data['tenant_id'],
                'created_by': data['created_by'],
                'doc_type': data['doc_type'],
                'customer_id': data.get('customer_id'),
                'currency': data.get('currency', 'CRC'),
                'issue_date': data.get('issue_date', datetime.now(UTC)),
                'status': DocumentStatus.DRAFT.value,
                'idempotency_key': data['idempotency_key'],
                'items': data['items'],
                'notes': data.get('notes'),
            }
            invoice = await uow.invoice_repository.create_draft(payload)
            await uow.event_repository.append_event(data['tenant_id'], invoice['id'], 'none', DocumentStatus.DRAFT.value, 'created')
            await uow.commit()
            return invoice
