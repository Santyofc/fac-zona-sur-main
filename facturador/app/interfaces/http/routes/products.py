from uuid import UUID

from fastapi import APIRouter, Depends

from app.interfaces.http.deps import build_invoice_use_cases, get_tenant_id
from app.interfaces.http.schemas.product_schemas import ProductIn

router = APIRouter(prefix='/v1/products', tags=['products'])


@router.post('')
async def create_product(data: ProductIn, tenant_id: UUID = Depends(get_tenant_id)):
    payload = data.model_dump()
    payload['tenant_id'] = tenant_id
    return await build_invoice_use_cases()['create_product'].execute(payload)


@router.get('')
async def list_products(tenant_id: UUID = Depends(get_tenant_id)):
    return await build_invoice_use_cases()['list_products'].execute(tenant_id)
