import asyncio
from uuid import UUID

from app.application.use_cases.invoices.get_invoice_status import GetInvoiceStatusUseCase
from app.infrastructure.db.uow.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.integrations.hacienda.client import HaciendaHTTPClient
from app.workers.celery_app import celery_app


@celery_app.task(name='app.workers.tasks.check_document_status.check_document_status_task', bind=True, max_retries=5)
def check_document_status_task(self, payload: dict):
    async def run():
        uc = GetInvoiceStatusUseCase(SQLAlchemyUnitOfWork(), HaciendaHTTPClient())
        return await uc.execute(UUID(payload['tenant_id']), UUID(payload['invoice_id']))

    try:
        return asyncio.run(run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
