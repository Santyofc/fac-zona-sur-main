from app.infrastructure.db.models.document_event_model import DocumentEventModel


class SQLAlchemyEventRepository:
    def __init__(self, session):
        self.session = session

    async def append_event(self, tenant_id, invoice_id, from_status, to_status, reason=None):
        self.session.add(
            DocumentEventModel(
                tenant_id=tenant_id,
                invoice_id=invoice_id,
                from_status=from_status,
                to_status=to_status,
                reason=reason,
            )
        )
