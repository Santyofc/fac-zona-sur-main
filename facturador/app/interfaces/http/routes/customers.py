from uuid import UUID

from fastapi import APIRouter, Depends

from app.interfaces.http.deps import build_invoice_use_cases, get_tenant_id
from app.interfaces.http.schemas.customer_schemas import CustomerIn

router = APIRouter(prefix='/v1/customers', tags=['customers'])


@router.post('')
async def create_customer(data: CustomerIn, tenant_id: UUID = Depends(get_tenant_id)):
    payload = data.model_dump()
    payload['tenant_id'] = tenant_id
    return await build_invoice_use_cases()['create_customer'].execute(payload)


@router.get('')
async def list_customers(tenant_id: UUID = Depends(get_tenant_id)):
    return await build_invoice_use_cases()['list_customers'].execute(tenant_id)
