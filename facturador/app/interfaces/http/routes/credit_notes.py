from uuid import UUID

from fastapi import APIRouter, Depends

from app.interfaces.http.deps import build_invoice_use_cases, get_tenant_id
from app.interfaces.http.schemas.invoice_schemas import InvoiceCreateIn, IssueInvoiceIn

router = APIRouter(prefix='/v1/credit-notes', tags=['credit-notes'])


@router.post('')
async def create_credit_note(data: InvoiceCreateIn, tenant_id: UUID = Depends(get_tenant_id)):
    payload = data.model_dump()
    payload['tenant_id'] = tenant_id
    payload['doc_type'] = 'NC'
    return await build_invoice_use_cases()['create_invoice'].execute(payload)


@router.post('/{credit_note_id}/issue')
async def issue_credit_note(credit_note_id: UUID, data: IssueInvoiceIn, tenant_id: UUID = Depends(get_tenant_id)):
    return await build_invoice_use_cases()['issue_invoice'].execute(tenant_id, credit_note_id, data.requested_by, data.idempotency_key)
