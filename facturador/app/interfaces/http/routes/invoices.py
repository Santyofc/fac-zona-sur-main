from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.interfaces.http.deps import build_invoice_use_cases, get_tenant_id
from app.interfaces.http.schemas.invoice_schemas import EmailInvoiceIn, InvoiceCreateIn, IssueInvoiceIn

router = APIRouter(prefix='/v1/invoices', tags=['invoices'])


@router.post('')
async def create_invoice(data: InvoiceCreateIn, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['create_invoice']
    payload = data.model_dump()
    payload['tenant_id'] = tenant_id
    result = await uc.execute(payload)
    return result


@router.get('')
async def list_invoices(tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['list_invoices']
    return await uc.execute(tenant_id)


@router.get('/{invoice_id}')
async def get_invoice(invoice_id: UUID, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['get_invoice']
    result = await uc.execute(tenant_id, invoice_id)
    if not result:
        raise HTTPException(status_code=404, detail='invoice not found')
    return result


@router.post('/{invoice_id}/issue')
async def issue_invoice(
    invoice_id: UUID,
    data: IssueInvoiceIn,
    async_mode: bool = Query(True),
    tenant_id: UUID = Depends(get_tenant_id),
):
    if async_mode:
        from app.infrastructure.integrations.queue.celery_dispatcher import CeleryJobDispatcher
        dispatcher = CeleryJobDispatcher()
        await dispatcher.dispatch_issue(
            {
                'tenant_id': str(tenant_id),
                'invoice_id': str(invoice_id),
                'requested_by': str(data.requested_by),
                'idempotency_key': data.idempotency_key,
            }
        )
        return {'status': 'queued', 'invoice_id': invoice_id}

    uc = build_invoice_use_cases()['issue_invoice']
    return await uc.execute(tenant_id, invoice_id, data.requested_by, data.idempotency_key)


@router.get('/{invoice_id}/status')
async def get_invoice_status(invoice_id: UUID, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['invoice_status']
    return await uc.execute(tenant_id, invoice_id)


@router.get('/{invoice_id}/xml')
async def get_invoice_xml(invoice_id: UUID, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['get_invoice']
    invoice = await uc.execute(tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail='invoice not found')
    return {'invoice_id': invoice_id, 'message': 'XML disponible en submission xml_signed_url'}


@router.get('/{invoice_id}/pdf')
async def get_invoice_pdf(invoice_id: UUID, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['get_invoice']
    invoice = await uc.execute(tenant_id, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail='invoice not found')
    return {'invoice_id': invoice_id, 'message': 'PDF disponible en submission pdf_url'}


@router.post('/{invoice_id}/email')
async def send_invoice_email(invoice_id: UUID, data: EmailInvoiceIn, tenant_id: UUID = Depends(get_tenant_id)):
    uc = build_invoice_use_cases()['send_invoice_email']
    return await uc.execute(tenant_id, invoice_id, data.recipient_email, data.idempotency_key)
