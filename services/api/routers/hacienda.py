"""
Hacienda Router — Envío y consulta de estado ante el Ministerio de Hacienda CR
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from config import get_settings
from database import get_db
from models.models import User, Invoice, HaciendaDocument
from schemas.schemas import HaciendaStatusResponse
from routers.deps import get_current_user
from services.invoice_hacienda_service import InvoiceHaciendaService

router = APIRouter()


@router.post("/{invoice_id}/hacienda/send", response_model=HaciendaStatusResponse)
async def send_to_hacienda(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Iniciar el proceso completo de envío a Hacienda:
    1. Generar XML
    2. Firmar XML
    3. Enviar a API Hacienda
    4. Guardar respuesta
    """
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items), selectinload(Invoice.client), selectinload(Invoice.hacienda_doc))
        .where(Invoice.id == invoice_id, Invoice.company_id == current_user.company_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    if invoice.status not in ("draft", "rejected", "sent"):
        raise HTTPException(
            status_code=409,
            detail=f"La factura en estado '{invoice.status}' no puede ser enviada."
        )

    if invoice.hacienda_doc and (invoice.hacienda_doc.hacienda_status or "").lower() in ("aceptado", "procesando", "recibido"):
        raise HTTPException(status_code=409, detail="Ya existe un envío activo o finalizado para esta factura.")

    service = InvoiceHaciendaService(db, get_settings())
    result = await service.process_invoice(str(invoice_id))

    hacienda_doc = invoice.hacienda_doc or HaciendaDocument(invoice_id=invoice.id, send_attempts=0)
    if not invoice.hacienda_doc:
        db.add(hacienda_doc)

    return HaciendaStatusResponse(
        invoice_id=invoice.id,
        status=result.get("status", invoice.status),
        hacienda_status=result.get("hacienda_status", hacienda_doc.hacienda_status),
        hacienda_msg=result.get("message", hacienda_doc.hacienda_msg),
        submission_date=hacienda_doc.submission_date,
        response_date=hacienda_doc.response_date,
        send_attempts=hacienda_doc.send_attempts or 0,
        pdf_url=hacienda_doc.pdf_url,
    )


@router.get("/{invoice_id}/hacienda/status", response_model=HaciendaStatusResponse)
async def get_hacienda_status(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Consultar el estado de una factura ante Hacienda."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.hacienda_doc))
        .where(Invoice.id == invoice_id, Invoice.company_id == current_user.company_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    hacienda_doc = invoice.hacienda_doc
    if not hacienda_doc:
        raise HTTPException(
            status_code=404,
            detail="Esta factura aún no ha sido enviada a Hacienda."
        )

    return HaciendaStatusResponse(
        invoice_id=invoice.id,
        status=invoice.status,
        hacienda_status=hacienda_doc.hacienda_status,
        hacienda_msg=hacienda_doc.hacienda_msg,
        submission_date=hacienda_doc.submission_date,
        response_date=hacienda_doc.response_date,
        send_attempts=hacienda_doc.send_attempts,
        pdf_url=hacienda_doc.pdf_url,
    )


@router.post("/{invoice_id}/hacienda/status/refresh", response_model=HaciendaStatusResponse)
async def refresh_hacienda_status(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Forzar una consulta de estado en tiempo real ante Hacienda y actualizar la DB.
    Este endpoint es consumido por el worker de fondo para sincronización masiva.
    """
    ownership = await db.execute(
        select(Invoice.id).where(Invoice.id == invoice_id, Invoice.company_id == current_user.company_id)
    )
    if ownership.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    service = InvoiceHaciendaService(db, get_settings())
    result = await service.check_status(str(invoice_id))

    return HaciendaStatusResponse(
        invoice_id=invoice_id,
        status=result.get("status", "processing"),
        hacienda_status=result.get("hacienda_status"),
        hacienda_msg=result.get("message"),
        submission_date=None,
        response_date=None,
        send_attempts=result.get("send_attempts", 0),
        pdf_url=None,
    )
