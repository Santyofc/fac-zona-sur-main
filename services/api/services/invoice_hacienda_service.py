"""
InvoiceHaciendaService — Capa de orquestación para el envío y consulta de facturas.
Maneja la lógica de negocio, mapeos de ORM a payload y persistencia de resultados.
"""

import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.models import Invoice, InvoiceItem, Company, Client, HaciendaDocument
from services.hacienda.hacienda import process_invoice as _process_hacienda_pipeline
from services.hacienda.check_status import check_status as _check_hacienda_status, ComprobanteStatus
from services.hacienda.auth_service import AuthService

logger = logging.getLogger(__name__)

class InvoiceHaciendaService:
    def __init__(self, db: AsyncSession, settings: Any):
        self.db = db
        self.settings = settings

    async def process_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Orquesta el envío de una factura a Hacienda:
        1. Carga datos (Factura, Items, Empresa, Cliente)
        2. Ejecuta pipeline de Hacienda
        3. Actualiza estados y persiste documentos
        """
        logger.info(f"🚀 Procesando factura {invoice_id} para Hacienda")

        # 1. Cargar datos
        invoice = await self._get_invoice(invoice_id)
        items = await self._get_items(invoice_id)
        company = await self._get_company(invoice.company_id)
        client_data = await self._get_client_data(invoice.client_id)

        # 2. Incrementar consecutivo atómico (Paso intermedio antes de Clave)
        company.consecutive_num = (company.consecutive_num or 0) + 1
        sequence_number = company.consecutive_num
        await self.db.flush()

        # 3. Preparar Payloads
        invoice_payload = self._map_invoice_to_payload(invoice, items, client_data, sequence_number)
        company_payload = self._map_company_to_payload(company)

        # 4. Llamar Pipeline de Hacienda (Sandbox/Prod)
        # Nota: aquí se genera la Clave y se firma el XML
        result = await _process_hacienda_pipeline(invoice_payload, company_payload, self.settings)

        # 5. Persistir resultados
        await self._update_invoice_status(invoice, result)
        await self._upsert_hacienda_document(invoice_id, result)

        await self.db.commit()
        
        return {
            "invoice_id": invoice_id,
            "clave": result["clave"],
            "status": result.get("hacienda_result", {}).get("hacienda_status", "processing"),
        }

    async def check_status(self, invoice_id: str) -> Dict[str, Any]:
        """Consulta el estado actual de una factura en Hacienda."""
        invoice = await self._get_invoice(invoice_id)
        if not invoice or not invoice.clave:
            raise ValueError("Factura no tiene clave asignada.")

        # Auth context
        auth = AuthService(
            username=self.settings.HACIENDA_USERNAME,
            password=self.settings.HACIENDA_PASSWORD,
            environment=getattr(self.settings, "HACIENDA_ENV", "sandbox"),
        )

        status_result = await _check_hacienda_status(
            clave=invoice.clave,
            auth=auth,
            environment=getattr(self.settings, "HACIENDA_ENV", "sandbox"),
        )

        # Actualizar estados
        invoice.status = "accepted" if status_result.status == ComprobanteStatus.ACEPTADO else \
                        "rejected" if status_result.status == ComprobanteStatus.RECHAZADO else \
                        "processing"
        
        # Actualizar HaciendaDocument
        hac_result = await self.db.execute(select(HaciendaDocument).where(HaciendaDocument.invoice_id == invoice_id))
        hac_doc = hac_result.scalar_one_or_none()
        if hac_doc:
            hac_doc.hacienda_status = status_result.status.value
            hac_doc.hacienda_msg = status_result.message
            hac_doc.response_date = datetime.now(timezone.utc)
            if status_result.respuesta_xml:
                hac_doc.response_xml = status_result.respuesta_xml

        await self.db.commit()

        return {
            "invoice_id": invoice_id,
            "status": invoice.status,
            "hacienda_status": status_result.status.value,
            "message": status_result.message
        }

    # ─── Privados ──────────────────────────────────────────────────────────

    async def _get_invoice(self, invoice_id: str) -> Invoice:
        res = await self.db.execute(select(Invoice).where(Invoice.id == invoice_id))
        obj = res.scalar_one_or_none()
        if not obj: raise ValueError(f"Invoice {invoice_id} not found")
        return obj

    async def _get_items(self, invoice_id: str):
        res = await self.db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id).order_by(InvoiceItem.line_number))
        return res.scalars().all()

    async def _get_company(self, company_id: str) -> Company:
        res = await self.db.execute(select(Company).where(Company.id == company_id))
        return res.scalar_one()

    async def _get_client_data(self, client_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not client_id: return None
        res = await self.db.execute(select(Client).where(Client.id == client_id))
        c = res.scalar_one_or_none()
        if not c: return None
        return {
            "name": c.name, "cedula_number": c.cedula_number, "cedula_type": c.cedula_type,
            "email": c.email, "province": c.province, "canton": c.canton,
            "district": c.district, "address": c.address
        }

    def _map_invoice_to_payload(self, invoice: Invoice, items, client, sequence):
        return {
            "doc_type": invoice.doc_type or "FE",
            "sequence_number": sequence,
            "currency": invoice.currency or "CRC",
            "exchange_rate": float(invoice.exchange_rate or 1.0),
            "sale_condition": invoice.sale_condition or "01",
            "payment_method": invoice.payment_method or "01",
            "notes": invoice.notes,
            "client": client,
            "items": [
                {
                    "cabys_code": i.cabys_code or "9999999999999",
                    "description": i.description,
                    "quantity": float(i.quantity),
                    "unit_price": float(i.unit_price),
                    "unit_measure": i.unit_measure or "Unid",
                    "discount_pct": float(i.discount_pct or 0),
                    "tax_rate": float(i.tax_rate or 13),
                } for i in items
            ]
        }

    def _map_company_to_payload(self, company: Company):
        return {
            "name": company.name, "trade_name": company.trade_name,
            "cedula_type": company.cedula_type, "cedula_number": company.cedula_number,
            "email": company.email, "phone": company.phone,
            "actividad_economica": getattr(company, "actividad_economica", "620200"),
            "ubicacion": {
                "provincia": company.province or "1", "canton": company.canton or "01",
                "distrito": company.district or "01", "otras_senas": company.address
            }
        }

    async def _update_invoice_status(self, invoice, result):
        invoice.clave = result["clave"]
        invoice.consecutive = result["consecutive"]
        invoice.issue_date = datetime.now(timezone(timedelta(hours=-6)))
        h_res = result.get("hacienda_result", {})
        invoice.status = "processing" if h_res.get("success") else "sent"

    async def _upsert_hacienda_document(self, invoice_id, result):
        h_res = result.get("hacienda_result", {})
        res = await self.db.execute(select(HaciendaDocument).where(HaciendaDocument.invoice_id == invoice_id))
        doc = res.scalar_one_or_none()
        if not doc:
            doc = HaciendaDocument(id=str(uuid4()), invoice_id=invoice_id)
            self.db.add(doc)
        
        doc.xml_filename = f"{result['clave']}.xml"
        doc.submission_date = datetime.now(timezone.utc)
        doc.hacienda_status = h_res.get("hacienda_status", "procesando")
        doc.hacienda_msg = h_res.get("message", "")
        doc.send_attempts = (doc.send_attempts or 0) + 1
        doc.last_attempt_at = datetime.now(timezone.utc)
