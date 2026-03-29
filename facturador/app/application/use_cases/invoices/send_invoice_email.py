from datetime import datetime


class SendInvoiceEmailUseCase:
    def __init__(self, uow, email_sender, storage_service):
        self.uow = uow
        self.email_sender = email_sender
        self.storage = storage_service

    async def execute(self, tenant_id, invoice_id, to_email, idempotency_key):
        async with self.uow as uow:
            latest = await uow.submission_repository.get_latest(tenant_id, invoice_id)
            if not latest:
                raise ValueError('invoice not issued yet')
            delivery = await self.email_sender.send({
                'tenant_id': tenant_id,
                'invoice_id': invoice_id,
                'to': to_email,
                'pdf_url': latest.get('pdf_url'),
                'xml_url': latest.get('xml_signed_url'),
                'idempotency_key': idempotency_key,
                'sent_at': datetime.utcnow().isoformat(),
            })
            await uow.commit()
            return delivery
