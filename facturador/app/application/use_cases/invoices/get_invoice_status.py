from app.domain.common.enums import DocumentStatus
from app.domain.billing.rules import validate_transition


class GetInvoiceStatusUseCase:
    def __init__(self, uow, hacienda_gateway):
        self.uow = uow
        self.hacienda_gateway = hacienda_gateway

    async def execute(self, tenant_id, invoice_id):
        async with self.uow as uow:
            invoice = await uow.invoice_repository.get_by_id(tenant_id, invoice_id)
            if not invoice or not invoice.get('clave'):
                return {'status': invoice['status'] if invoice else 'not_found'}

            status = await self.hacienda_gateway.get_status(invoice['clave'])
            mapped = 'submitted'
            if status['hacienda_status'] == 'aceptado':
                mapped = 'accepted'
            elif status['hacienda_status'] == 'rechazado':
                mapped = 'rejected'

            current = DocumentStatus(invoice['status'])
            target = DocumentStatus(mapped)
            if current != target:
                validate_transition(current, target)
                await uow.invoice_repository.update_status(tenant_id, invoice_id, mapped)
                await uow.event_repository.append_event(tenant_id, invoice_id, current.value, target.value, status.get('message'))
            await uow.commit()
            return {'status': mapped, 'hacienda': status}
