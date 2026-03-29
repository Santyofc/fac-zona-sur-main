import uuid

import pytest

from app.application.use_cases.invoices.get_invoice_status import GetInvoiceStatusUseCase


class FakeInvoiceRepo:
    def __init__(self):
        self.invoice = {
            'id': uuid.uuid4(),
            'status': 'submitted',
            'clave': '50601010101010101010101010101010101010101010101010',
        }

    async def get_by_id(self, tenant_id, invoice_id):
        return self.invoice

    async def update_status(self, tenant_id, invoice_id, status):
        self.invoice['status'] = status


class FakeEventRepo:
    def __init__(self):
        self.events = []

    async def append_event(self, *args, **kwargs):
        self.events.append((args, kwargs))


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


class FakeHacienda:
    async def get_status(self, clave):
        return {'hacienda_status': 'aceptado', 'message': 'ok'}


@pytest.mark.asyncio
async def test_status_sync_updates_document_status():
    uow = FakeUOW()
    uc = GetInvoiceStatusUseCase(uow, FakeHacienda())
    result = await uc.execute(uuid.uuid4(), uuid.uuid4())
    assert result['status'] == 'accepted'
    assert uow.invoice_repository.invoice['status'] == 'accepted'
