from sqlalchemy import select, update

from app.infrastructure.db.models.certificate_model import CertificateModel


class SQLAlchemyCertificateRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, payload: dict) -> dict:
        await self.session.execute(
            update(CertificateModel)
            .where(CertificateModel.tenant_id == payload['tenant_id'])
            .values(is_active=False)
        )
        row = CertificateModel(**payload)
        self.session.add(row)
        await self.session.flush()
        return {'id': row.id, 'tenant_id': row.tenant_id, 'alias': row.alias, 'p12_path': row.p12_path, 'is_active': row.is_active}

    async def get_active(self, tenant_id):
        result = await self.session.execute(
            select(CertificateModel).where(CertificateModel.tenant_id == tenant_id, CertificateModel.is_active == True)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {'id': row.id, 'tenant_id': row.tenant_id, 'alias': row.alias, 'p12_path': row.p12_path, 'p12_password': row.p12_password, 'is_active': row.is_active}
