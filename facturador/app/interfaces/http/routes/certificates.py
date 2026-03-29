from uuid import UUID

from fastapi import APIRouter, Depends

from app.interfaces.http.deps import build_invoice_use_cases, get_tenant_id
from app.interfaces.http.schemas.certificate_schemas import CertificateIn

router = APIRouter(prefix='/v1/certificates', tags=['certificates'])


@router.post('')
async def upload_certificate(data: CertificateIn, tenant_id: UUID = Depends(get_tenant_id)):
    payload = data.model_dump()
    payload['tenant_id'] = tenant_id
    return await build_invoice_use_cases()['upload_certificate'].execute(payload)
