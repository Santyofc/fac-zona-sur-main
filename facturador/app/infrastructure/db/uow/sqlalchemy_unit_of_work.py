from app.infrastructure.db.repositories.sqlalchemy_certificate_repository import SQLAlchemyCertificateRepository
from app.infrastructure.db.repositories.sqlalchemy_customer_repository import SQLAlchemyCustomerRepository
from app.infrastructure.db.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from app.infrastructure.db.repositories.sqlalchemy_invoice_repository import SQLAlchemyInvoiceRepository
from app.infrastructure.db.repositories.sqlalchemy_product_repository import SQLAlchemyProductRepository
from app.infrastructure.db.repositories.sqlalchemy_sequence_repository import SQLAlchemySequenceRepository
from app.infrastructure.db.repositories.sqlalchemy_submission_repository import SQLAlchemySubmissionRepository
from app.infrastructure.db.session import SessionLocal


class SQLAlchemyUnitOfWork:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = SessionLocal()
        self.invoice_repository = SQLAlchemyInvoiceRepository(self.session)
        self.customer_repository = SQLAlchemyCustomerRepository(self.session)
        self.product_repository = SQLAlchemyProductRepository(self.session)
        self.certificate_repository = SQLAlchemyCertificateRepository(self.session)
        self.sequence_repository = SQLAlchemySequenceRepository(self.session)
        self.event_repository = SQLAlchemyEventRepository(self.session)
        self.submission_repository = SQLAlchemySubmissionRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
