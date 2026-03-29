import asyncio
from uuid import UUID

from app.application.use_cases.invoices.send_invoice_email import SendInvoiceEmailUseCase
from app.infrastructure.db.uow.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.integrations.email.sender import LocalEmailSender
from app.infrastructure.integrations.storage.local_storage import LocalStorageService
from app.workers.celery_app import celery_app


@celery_app.task(name='app.workers.tasks.send_document_email.send_document_email_task', bind=True, max_retries=5)
def send_document_email_task(self, payload: dict):
    async def run():
        uc = SendInvoiceEmailUseCase(SQLAlchemyUnitOfWork(), LocalEmailSender(), LocalStorageService())
        return await uc.execute(
            UUID(payload['tenant_id']),
            UUID(payload['invoice_id']),
            payload['recipient_email'],
            payload['idempotency_key'],
        )

    try:
        return asyncio.run(run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
