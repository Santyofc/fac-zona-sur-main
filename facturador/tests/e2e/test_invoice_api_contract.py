import uuid
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app


class _StubCreateInvoiceUseCase:
    async def execute(self, payload):
        return {
            "id": str(uuid.uuid4()),
            "tenant_id": str(payload["tenant_id"]),
            "status": "draft",
        }


def test_create_invoice_contract_shape(monkeypatch):
    monkeypatch.setattr(
        "app.interfaces.http.routes.invoices.build_invoice_use_cases",
        lambda: {"create_invoice": _StubCreateInvoiceUseCase()},
    )
    client = TestClient(app, raise_server_exceptions=False)
    tenant_id = str(uuid.uuid4())
    payload = {
        'customer_id': None,
        'doc_type': 'FE',
        'currency': 'CRC',
        'issue_date': datetime.now(UTC).isoformat(),
        'notes': 'test',
        'idempotency_key': 'e2e-key-1',
        'created_by': str(uuid.uuid4()),
        'items': [
            {'description': 'Servicio', 'cabys_code': '0000000000000', 'quantity': 1, 'unit_price': 1000, 'discount_pct': 0, 'tax_rate': 13}
        ],
    }
    response = client.post('/v1/invoices', json=payload, headers={'X-Tenant-Id': tenant_id})
    assert response.status_code in (200, 201)
