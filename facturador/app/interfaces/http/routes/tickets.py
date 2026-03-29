from uuid import UUID

from fastapi import APIRouter, Depends

from app.interfaces.http.deps import build_invoice_use_cases, get_tenant_id
from app.interfaces.http.schemas.invoice_schemas import InvoiceCreateIn, IssueInvoiceIn

router = APIRouter(prefix='/v1/tickets', tags=['tickets'])


@router.post('')
async def create_ticket(data: InvoiceCreateIn, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['create_invoice']
    payload = data.model_dump()
    payload['tenant_id'] = tenant_id
    payload['doc_type'] = 'TE'
    return await uc.execute(payload)


@router.post('/{ticket_id}/issue')
async def issue_ticket(ticket_id: UUID, data: IssueInvoiceIn, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['issue_invoice']
    return await uc.execute(tenant_id, ticket_id, data.requested_by, data.idempotency_key)
