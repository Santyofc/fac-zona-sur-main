from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.infrastructure.db.base import Base
from app.infrastructure.db.models.audit_log_model import AuditLogModel
from app.infrastructure.db.models.certificate_model import CertificateModel
from app.infrastructure.db.models.customer_model import CustomerModel
from app.infrastructure.db.models.document_event_model import DocumentEventModel
from app.infrastructure.db.models.email_delivery_model import EmailDeliveryModel
from app.infrastructure.db.models.hacienda_submission_model import HaciendaSubmissionModel
from app.infrastructure.db.models.invoice_item_model import InvoiceItemModel
from app.infrastructure.db.models.invoice_model import InvoiceModel
from app.infrastructure.db.models.invoice_tax_model import InvoiceTaxModel
from app.infrastructure.db.models.product_model import ProductModel
from app.infrastructure.db.models.sequence_model import SequenceModel
from app.infrastructure.db.models.tenant_model import TenantModel
from app.infrastructure.db.models.user_model import UserModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option('sqlalchemy.url')
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
