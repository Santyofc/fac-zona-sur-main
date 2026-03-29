from sqlalchemy import select

from app.infrastructure.db.models.product_model import ProductModel


class SQLAlchemyProductRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, payload: dict) -> dict:
        row = ProductModel(**payload)
        self.session.add(row)
        await self.session.flush()
        return {
            'id': row.id,
            'tenant_id': row.tenant_id,
            'code': row.code,
            'name': row.name,
            'cabys_code': row.cabys_code,
            'unit_price': row.unit_price,
            'tax_rate': row.tax_rate,
        }

    async def list_by_tenant(self, tenant_id):
        result = await self.session.execute(select(ProductModel).where(ProductModel.tenant_id == tenant_id))
        rows = result.scalars().all()
        return [{'id': r.id, 'code': r.code, 'name': r.name, 'cabys_code': r.cabys_code, 'unit_price': r.unit_price, 'tax_rate': r.tax_rate} for r in rows]
