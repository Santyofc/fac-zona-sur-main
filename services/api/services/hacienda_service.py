"""
Compatibility wrappers for Hacienda operations.
Delegates to InvoiceHaciendaService to keep a single source of truth for
idempotency, retries and status transitions.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from services.invoice_hacienda_service import InvoiceHaciendaService


async def process_invoice_to_hacienda(
    invoice_id: str,
    db: AsyncSession,
    config=None,
) -> dict:
    service = InvoiceHaciendaService(db, config or settings)
    return await service.process_invoice(invoice_id)


async def refresh_invoice_status(
    invoice_id: str,
    db: AsyncSession,
) -> dict:
    service = InvoiceHaciendaService(db, settings)
    result = await service.check_status(invoice_id)
    return {
        "invoice_id": result.get("invoice_id"),
        "status": result.get("status"),
        "hacienda_status": result.get("hacienda_status"),
        "hacienda_msg": result.get("message"),
        "submission_date": None,
        "response_date": None,
        "send_attempts": result.get("send_attempts", 0),
        "pdf_url": None,
    }
