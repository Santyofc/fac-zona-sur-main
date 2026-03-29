from fastapi import Header, HTTPException
from uuid import UUID

from app.application.use_cases.certificates.upload_certificate import UploadCertificateUseCase
from app.application.use_cases.customers.create_customer import CreateCustomerUseCase
from app.application.use_cases.customers.list_customers import ListCustomersUseCase
from app.application.use_cases.invoices.create_invoice import CreateInvoiceUseCase
from app.application.use_cases.invoices.get_invoice import GetInvoiceUseCase
from app.application.use_cases.invoices.get_invoice_status import GetInvoiceStatusUseCase
from app.application.use_cases.invoices.issue_invoice import IssueInvoiceUseCase
from app.application.use_cases.invoices.list_invoices import ListInvoicesUseCase
from app.application.use_cases.invoices.send_invoice_email import SendInvoiceEmailUseCase
from app.application.use_cases.products.create_product import CreateProductUseCase
from app.application.use_cases.products.list_products import ListProductsUseCase
from app.infrastructure.db.uow.sqlalchemy_unit_of_work import SQLAlchemyUnitOfWork
from app.infrastructure.integrations.email.sender import LocalEmailSender
from app.infrastructure.integrations.hacienda.client import HaciendaHTTPClient
from app.infrastructure.integrations.pdf.renderer import SimplePDFRenderer
from app.infrastructure.integrations.storage.local_storage import LocalStorageService
from app.infrastructure.integrations.xml.builder_44 import XML44Builder
from app.infrastructure.integrations.xml.signer_xades import XAdESSigner


def get_tenant_id(x_tenant_id: str = Header(..., alias='X-Tenant-Id')) -> UUID:
    try:
        return UUID(x_tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail='invalid tenant id') from exc


def get_uow() -> SQLAlchemyUnitOfWork:
    return SQLAlchemyUnitOfWork()


def build_invoice_use_cases() -> dict:
    uow = SQLAlchemyUnitOfWork()
    xml_builder = XML44Builder()
    xml_signer = XAdESSigner()
    hacienda = HaciendaHTTPClient()
    storage = LocalStorageService()
    pdf = SimplePDFRenderer()
    email = LocalEmailSender()

    return {
        'create_invoice': CreateInvoiceUseCase(uow),
        'list_invoices': ListInvoicesUseCase(uow),
        'get_invoice': GetInvoiceUseCase(uow),
        'issue_invoice': IssueInvoiceUseCase(uow, xml_builder, xml_signer, hacienda, storage, pdf),
        'invoice_status': GetInvoiceStatusUseCase(uow, hacienda),
        'send_invoice_email': SendInvoiceEmailUseCase(uow, email, storage),
        'create_customer': CreateCustomerUseCase(uow),
        'list_customers': ListCustomersUseCase(uow),
        'create_product': CreateProductUseCase(uow),
        'list_products': ListProductsUseCase(uow),
        'upload_certificate': UploadCertificateUseCase(uow),
    }
