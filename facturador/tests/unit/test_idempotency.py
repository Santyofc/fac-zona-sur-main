import uuid
from datetime import UTC, datetime

import pytest

from app.application.use_cases.invoices.create_invoice import CreateInvoiceUseCase


class FakeInvoiceRepo:
    def __init__(self):
        self.by_key = {}
        self.rows = []

    async def create_draft(self, payload):
        row = {'id': uuid.uuid4(), **payload, 'total': 100}
        self.by_key[(payload['tenant_id'], payload['idempotency_key'])] = row
        self.rows.append(row)
        return row

    async def find_by_idempotency_key(self, tenant_id, key):
        return self.by_key.get((tenant_id, key))


class FakeEventRepo:
    async def append_event(self, *args, **kwargs):
        return None


class FakeUOW:
    def __init__(self):
        self.invoice_repository = FakeInvoiceRepo()
        self.event_repository = FakeEventRepo()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def commit(self):
        return None


@pytest.mark.asyncio
async def test_create_invoice_idempotent():
    uow = FakeUOW()
    uc = CreateInvoiceUseCase(uow)
    payload = {
        'tenant_id': uuid.uuid4(),
        'created_by': uuid.uuid4(),
        'doc_type': 'FE',
        'currency': 'CRC',
        'issue_date': datetime.now(UTC),
        'idempotency_key': 'abc',
        'items': [{'description': 'x', 'quantity': 1, 'unit_price': 10}],
    }
    first = await uc.execute(payload)
    second = await uc.execute(payload)
    assert first['id'] == second['id']
    assert len(uow.invoice_repository.rows) == 1
