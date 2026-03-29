from datetime import datetime

from app.domain.billing.rules import generate_clave, generate_consecutive, validate_transition
from app.domain.common.enums import DocumentStatus


class IssueInvoiceUseCase:
    def __init__(self, uow, xml_builder, xml_signer, hacienda_gateway, storage_service, pdf_renderer):
        self.uow = uow
        self.xml_builder = xml_builder
        self.xml_signer = xml_signer
        self.hacienda_gateway = hacienda_gateway
        self.storage = storage_service
        self.pdf = pdf_renderer

    async def execute(self, tenant_id, invoice_id, requested_by, idempotency_key):
        async with self.uow as uow:
            invoice = await uow.invoice_repository.get_by_id(tenant_id, invoice_id)
            if not invoice:
                raise ValueError('invoice not found')
            latest = await uow.submission_repository.get_latest(tenant_id, invoice_id)
            if latest and latest.get('idempotency_key') == idempotency_key:
                return latest

            cert = await uow.certificate_repository.get_active(tenant_id)
            if not cert:
                raise ValueError('active certificate required')

            current = DocumentStatus(invoice['status'])
            validate_transition(current, DocumentStatus.QUEUED)
            await uow.invoice_repository.update_status(tenant_id, invoice_id, DocumentStatus.QUEUED.value)
            await uow.event_repository.append_event(tenant_id, invoice_id, current.value, DocumentStatus.QUEUED.value, 'issue_start')

            sequence = await uow.sequence_repository.next_sequence(tenant_id, 1, 1, invoice['doc_type'])
            issue_payload = dict(invoice)
            issue_payload['sequence_number'] = sequence
            issue_payload['consecutive'] = generate_consecutive(sequence, invoice['doc_type'], 1, 1)
            issue_payload['clave'] = generate_clave('000000000000', issue_payload['consecutive'], invoice['issue_date'])

            xml_unsigned = await self.xml_builder.build(issue_payload)
            xml_key = f"{tenant_id}/{invoice_id}/unsigned.xml"
            unsigned_url = await self.storage.put_text(xml_key, xml_unsigned)

            signed = await self.xml_signer.sign(xml_unsigned, cert['p12_path'], cert['p12_password'])
            signed_key = f"{tenant_id}/{invoice_id}/signed.xml"
            signed_url = await self.storage.put_text(signed_key, signed)

            validate_transition(DocumentStatus.QUEUED, DocumentStatus.SIGNED)
            await uow.invoice_repository.update_status(tenant_id, invoice_id, DocumentStatus.SIGNED.value)
            await uow.event_repository.append_event(tenant_id, invoice_id, DocumentStatus.QUEUED.value, DocumentStatus.SIGNED.value, 'xml_signed')

            hac_res = await self.hacienda_gateway.submit(
                {
                    'clave': issue_payload['clave'],
                    'consecutive': issue_payload['consecutive'],
                    'issue_date': invoice['issue_date'],
                    'xml_signed': signed,
                    'emisor': {'tipoIdentificacion': '02', 'numeroIdentificacion': '000000000000'},
                }
            )

            validate_transition(DocumentStatus.SIGNED, DocumentStatus.SUBMITTED)
            await uow.invoice_repository.update_status(tenant_id, invoice_id, DocumentStatus.SUBMITTED.value)
            await uow.event_repository.append_event(tenant_id, invoice_id, DocumentStatus.SIGNED.value, DocumentStatus.SUBMITTED.value, hac_res.get('message'))

            pdf = await self.pdf.render(issue_payload)
            pdf_url = await self.storage.put_bytes(f"{tenant_id}/{invoice_id}/invoice.pdf", pdf)

            submission = await uow.submission_repository.create_submission({
                'tenant_id': tenant_id,
                'invoice_id': invoice_id,
                'idempotency_key': idempotency_key,
                'xml_unsigned_url': unsigned_url,
                'xml_signed_url': signed_url,
                'hacienda_payload': hac_res,
                'pdf_url': pdf_url,
                'submitted_at': datetime.utcnow(),
            })
            await uow.invoice_repository.update_issue_payload(tenant_id, invoice_id, {
                'consecutive': hac_res.get('consecutive'),
                'clave': hac_res.get('clave'),
                'status': DocumentStatus.SUBMITTED.value,
            })
            await uow.commit()
            return submission
