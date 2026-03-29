from sqlalchemy import select

from app.infrastructure.db.models.hacienda_submission_model import HaciendaSubmissionModel


class SQLAlchemySubmissionRepository:
    def __init__(self, session):
        self.session = session

    async def create_submission(self, payload: dict):
        row = HaciendaSubmissionModel(**payload)
        self.session.add(row)
        await self.session.flush()
        return {
            'id': row.id,
            'tenant_id': row.tenant_id,
            'invoice_id': row.invoice_id,
            'idempotency_key': row.idempotency_key,
            'xml_unsigned_url': row.xml_unsigned_url,
            'xml_signed_url': row.xml_signed_url,
            'pdf_url': row.pdf_url,
            'hacienda_payload': row.hacienda_payload,
        }

    async def get_latest(self, tenant_id, invoice_id):
        result = await self.session.execute(
            select(HaciendaSubmissionModel)
            .where(HaciendaSubmissionModel.tenant_id == tenant_id, HaciendaSubmissionModel.invoice_id == invoice_id)
            .order_by(HaciendaSubmissionModel.submitted_at.desc())
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return {
            'id': row.id,
            'tenant_id': row.tenant_id,
            'invoice_id': row.invoice_id,
            'idempotency_key': row.idempotency_key,
            'xml_unsigned_url': row.xml_unsigned_url,
            'xml_signed_url': row.xml_signed_url,
            'pdf_url': row.pdf_url,
            'hacienda_payload': row.hacienda_payload,
        }
