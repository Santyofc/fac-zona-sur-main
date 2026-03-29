"""
InvoiceHaciendaService — orchestration for Hacienda send / polling with
idempotency and row-level locking.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.models import Company, Client, HaciendaDocument, Invoice, InvoiceItem
from services.hacienda.auth_service import AuthService
from services.hacienda.check_status import (
    ComprobanteStatus,
    StatusResult,
    check_status as _check_hacienda_status,
)
from services.hacienda.hacienda import process_invoice as _process_hacienda_pipeline
from services.hacienda.clave import DocType as HaciendaDocType, generate_clave

logger = logging.getLogger(__name__)

FINAL_HACIENDA_STATUSES = {"aceptado", "rechazado"}
IN_FLIGHT_HACIENDA_STATUSES = {"procesando", "recibido"}


class RetryableHaciendaError(RuntimeError):
    """Raised when the worker should retry the send operation."""


class InvoiceHaciendaService:
    def __init__(self, db: AsyncSession, settings: Any):
        self.db = db
        self.settings = settings

    async def process_invoice(self, invoice_id: str) -> Dict[str, Any]:
        """
        Send one invoice to Hacienda, safely.

        Guarantees:
        - does not allocate a second consecutive if one is already reserved
        - avoids duplicate external submissions when a previous attempt likely succeeded
        - updates DB state deterministically under row locks
        """
        logger.info("🚀 Procesando factura %s para Hacienda", invoice_id)

        invoice = await self._get_invoice(invoice_id, for_update=True)
        hac_doc = await self._get_or_create_hacienda_document(invoice.id)

        if invoice.status == "accepted" or (hac_doc.hacienda_status or "") == "aceptado":
            await self.db.commit()
            return self._build_response(invoice, hac_doc)

        company = await self._get_company(invoice.company_id, for_update=not bool(invoice.consecutive and invoice.clave))
        items = await self._get_items(invoice_id)
        client_data = await self._get_client_data(invoice.client_id)

        await self._ensure_invoice_identifiers(invoice, company)

        if invoice.clave and (hac_doc.send_attempts or 0) > 0:
            status_result = await self._check_existing_status(invoice.clave)
            if status_result and status_result.status != ComprobanteStatus.NO_ENCONTRADO:
                await self._apply_status_result(invoice, hac_doc, status_result)
                await self.db.commit()
                return self._build_response(invoice, hac_doc)

        invoice_payload = self._map_invoice_to_payload(invoice, items, client_data)
        company_payload = self._map_company_to_payload(company)

        invoice.status = "processing"
        hac_doc.send_attempts = (hac_doc.send_attempts or 0) + 1
        hac_doc.last_attempt_at = datetime.now(timezone.utc)
        await self.db.commit()

        result = await _process_hacienda_pipeline(invoice_payload, company_payload, self.settings)
        hac_result = result.get("hacienda_result") or {}
        is_retryable = self._is_retryable_hacienda_result(hac_result)

        invoice = await self._get_invoice(invoice_id, for_update=True)
        hac_doc = await self._get_or_create_hacienda_document(invoice.id)
        await self._apply_pipeline_result(invoice, hac_doc, result)
        await self.db.commit()

        if is_retryable:
            raise RetryableHaciendaError(hac_result.get("message", "Fallo temporal enviando a Hacienda"))

        return self._build_response(invoice, hac_doc)

    async def check_status(self, invoice_id: str) -> Dict[str, Any]:
        """Synchronize the current invoice state with Hacienda."""
        invoice = await self._get_invoice(invoice_id, for_update=True)
        if not invoice.clave:
            raise ValueError("Factura no tiene clave asignada.")

        hac_doc = await self._get_or_create_hacienda_document(invoice.id)
        status_result = await self._fetch_remote_status(invoice.clave)
        await self._apply_status_result(invoice, hac_doc, status_result)
        await self.db.commit()
        return self._build_response(invoice, hac_doc)

    async def _get_invoice(self, invoice_id: str, for_update: bool = False) -> Invoice:
        stmt = (
            select(Invoice)
            .options(selectinload(Invoice.hacienda_doc))
            .where(Invoice.id == invoice_id)
        )
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        obj = res.scalar_one_or_none()
        if not obj:
            raise ValueError(f"Invoice {invoice_id} not found")
        return obj

    async def _get_items(self, invoice_id: str):
        res = await self.db.execute(
            select(InvoiceItem)
            .where(InvoiceItem.invoice_id == invoice_id)
            .order_by(InvoiceItem.line_number)
        )
        return res.scalars().all()

    async def _get_company(self, company_id: str, for_update: bool = False) -> Company:
        stmt = select(Company).where(Company.id == company_id)
        if for_update:
            stmt = stmt.with_for_update()
        res = await self.db.execute(stmt)
        return res.scalar_one()

    async def _get_client_data(self, client_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not client_id:
            return None
        res = await self.db.execute(select(Client).where(Client.id == client_id))
        c = res.scalar_one_or_none()
        if not c:
            return None
        return {
            "name": c.name,
            "cedula_number": c.cedula_number,
            "cedula_type": c.cedula_type,
            "email": c.email,
            "province": c.province,
            "canton": c.canton,
            "district": c.district,
            "address": c.address,
        }

    async def _get_or_create_hacienda_document(self, invoice_id) -> HaciendaDocument:
        res = await self.db.execute(
            select(HaciendaDocument)
            .where(HaciendaDocument.invoice_id == invoice_id)
            .with_for_update()
        )
        doc = res.scalar_one_or_none()
        if not doc:
            doc = HaciendaDocument(
                id=str(uuid4()),
                invoice_id=invoice_id,
                send_attempts=0,
                hacienda_status="pendiente",
            )
            self.db.add(doc)
            await self.db.flush()
        return doc

    async def _ensure_invoice_identifiers(self, invoice: Invoice, company: Company) -> None:
        if invoice.consecutive and invoice.clave:
            return

        doc_type = {
            "FE": HaciendaDocType.FACTURA_ELECTRONICA,
            "TE": HaciendaDocType.TIQUETE_ELECTRONICO,
            "NC": HaciendaDocType.NOTA_CREDITO,
            "ND": HaciendaDocType.NOTA_DEBITO,
        }.get(invoice.doc_type or "FE", HaciendaDocType.FACTURA_ELECTRONICA)

        sequence_number = int(company.consecutive_num or 1)
        clave, consecutive = generate_clave(
            cedula=company.cedula_number,
            sequence_number=sequence_number,
            doc_type=doc_type,
        )

        invoice.consecutive = consecutive
        invoice.clave = clave
        company.consecutive_num = sequence_number + 1
        await self.db.flush()

    async def _check_existing_status(self, clave: str) -> Optional[StatusResult]:
        try:
            return await self._fetch_remote_status(clave)
        except Exception as exc:
            logger.warning("No se pudo verificar estado previo de %s antes de reenviar: %s", clave[:20], exc)
            return None

    async def _fetch_remote_status(self, clave: str) -> StatusResult:
        auth = AuthService(
            username=self.settings.HACIENDA_USERNAME,
            password=self.settings.HACIENDA_PASSWORD,
            environment=getattr(self.settings, "HACIENDA_ENV", "sandbox"),
        )
        return await _check_hacienda_status(
            clave=clave,
            auth=auth,
            environment=getattr(self.settings, "HACIENDA_ENV", "sandbox"),
        )

    def _map_invoice_to_payload(self, invoice: Invoice, items, client):
        sequence = int(invoice.consecutive[-10:]) if invoice.consecutive else 1
        return {
            "doc_type": invoice.doc_type or "FE",
            "sequence_number": sequence,
            "consecutive": invoice.consecutive,
            "clave": invoice.clave,
            "currency": invoice.currency or "CRC",
            "exchange_rate": float(invoice.exchange_rate or 1.0),
            "sale_condition": invoice.sale_condition or "01",
            "payment_method": invoice.payment_method or "01",
            "credit_term_days": invoice.credit_term_days,
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
                }
                for i in items
            ],
        }

    def _map_company_to_payload(self, company: Company):
        return {
            "name": company.name,
            "trade_name": company.trade_name,
            "cedula_type": company.cedula_type,
            "cedula_number": company.cedula_number,
            "email": company.email,
            "phone": company.phone,
            "actividad_economica": getattr(company, "actividad_economica", None)
            or getattr(company, "economic_activity", None)
            or "620200",
            "ubicacion": {
                "provincia": company.province or "1",
                "canton": company.canton or "01",
                "distrito": company.district or "01",
                "otras_senas": company.address,
            },
        }

    async def _apply_pipeline_result(self, invoice: Invoice, doc: HaciendaDocument, result: Dict[str, Any]) -> None:
        invoice.clave = result["clave"]
        invoice.consecutive = result["consecutive"]
        invoice.issue_date = datetime.now(timezone(timedelta(hours=-6)))

        h_res = result.get("hacienda_result") or {}
        status = (h_res.get("hacienda_status") or "").lower()
        message = h_res.get("message") or h_res.get("error") or ""

        doc.xml_filename = f"{result['clave']}.xml"
        doc.xml_signed = result.get("xml")
        doc.submission_date = datetime.now(timezone.utc)
        doc.hacienda_status = status or "error"
        doc.hacienda_msg = message
        doc.hacienda_detail = str(h_res.get("detail") or "")[:4000] or None
        doc.last_attempt_at = datetime.now(timezone.utc)

        if status == "aceptado":
            invoice.status = "accepted"
        elif status == "rechazado":
            invoice.status = "rejected"
        elif status in IN_FLIGHT_HACIENDA_STATUSES or h_res.get("success"):
            invoice.status = "sent"
        else:
            invoice.status = "rejected" if not self._is_retryable_hacienda_result(h_res) else "processing"

    async def _apply_status_result(self, invoice: Invoice, doc: HaciendaDocument, status_result: StatusResult) -> None:
        doc.hacienda_status = status_result.status.value
        doc.hacienda_msg = status_result.message
        doc.response_date = datetime.now(timezone.utc)
        doc.response_xml = status_result.respuesta_xml

        if status_result.status == ComprobanteStatus.ACEPTADO:
            invoice.status = "accepted"
        elif status_result.status == ComprobanteStatus.RECHAZADO:
            invoice.status = "rejected"
        elif status_result.status in (ComprobanteStatus.PROCESANDO, ComprobanteStatus.NO_ENCONTRADO):
            invoice.status = "processing"
        else:
            invoice.status = "processing"

    def _is_retryable_hacienda_result(self, h_res: Dict[str, Any]) -> bool:
        status_code = h_res.get("status_code")
        status = (h_res.get("hacienda_status") or "").lower()
        if status in FINAL_HACIENDA_STATUSES:
            return False
        if status_code in (400, 401):
            return False
        if status_code is None:
            return True
        try:
            code = int(status_code)
        except (TypeError, ValueError):
            return True
        return code == 0 or code >= 500

    def _build_response(self, invoice: Invoice, doc: HaciendaDocument) -> Dict[str, Any]:
        return {
            "invoice_id": str(invoice.id),
            "clave": invoice.clave,
            "status": invoice.status,
            "hacienda_status": doc.hacienda_status,
            "message": doc.hacienda_msg,
            "send_attempts": doc.send_attempts,
        }
