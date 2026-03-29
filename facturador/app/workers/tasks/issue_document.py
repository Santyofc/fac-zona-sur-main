import asyncio
from uuid import UUID

from app.application.use_cases.invoices.issue_invoice import IssueInvoiceUseCase
from app.infrastructure.db.uow.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.integrations.hacienda.client import HaciendaHTTPClient
from app.infrastructure.integrations.pdf.renderer import SimplePDFRenderer
from app.infrastructure.integrations.storage.local_storage import LocalStorageService
from app.infrastructure.integrations.xml.builder_44 import XML44Builder
from app.infrastructure.integrations.xml.signer_xades import XAdESSigner
from app.workers.celery_app import celery_app


@celery_app.task(name='app.workers.tasks.issue_document.issue_document_task', bind=True, max_retries=5)
def issue_document_task(self, payload: dict):
    async def run():
        uc = IssueInvoiceUseCase(
            SQLAlchemyUnitOfWork(),
            XML44Builder(),
            XAdESSigner(),
            HaciendaHTTPClient(),
            LocalStorageService(),
            SimplePDFRenderer(),
        )
        return await uc.execute(
            UUID(payload['tenant_id']),
            UUID(payload['invoice_id']),
            UUID(payload['requested_by']),
            payload['idempotency_key'],
        )

    try:
        return asyncio.run(run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
