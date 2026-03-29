from sqlalchemy import select

from app.infrastructure.db.models.customer_model import CustomerModel


class SQLAlchemyCustomerRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, payload: dict) -> dict:
        row = CustomerModel(**payload)
        self.session.add(row)
        await self.session.flush()
        return {
            'id': row.id,
            'tenant_id': row.tenant_id,
            'name': row.name,
            'email': row.email,
            'id_type': row.id_type,
            'id_number': row.id_number,
        }

    async def list_by_tenant(self, tenant_id):
        result = await self.session.execute(select(CustomerModel).where(CustomerModel.tenant_id == tenant_id))
        rows = result.scalars().all()
        return [{'id': r.id, 'name': r.name, 'email': r.email, 'id_type': r.id_type, 'id_number': r.id_number} for r in rows]
