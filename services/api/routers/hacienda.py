"""
Hacienda Router — Envío y consulta de estado ante el Ministerio de Hacienda CR
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID

from database import get_db
from models.models import User, Invoice, HaciendaDocument
from schemas.schemas import HaciendaStatusResponse
from routers.deps import get_current_user
from services.hacienda_service import process_invoice_to_hacienda

router = APIRouter()


@router.post("/{invoice_id}/send", response_model=HaciendaStatusResponse)
async def send_to_hacienda(
    invoice_id: UUID,
    background_tasks: BackgroundTasks,
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

    if invoice.status not in ("draft", "rejected"):
        raise HTTPException(
            status_code=400,
            detail=f"La factura en estado '{invoice.status}' no puede ser enviada."
        )

    # Create or reset HaciendaDocument
    if not invoice.hacienda_doc:
        hacienda_doc = HaciendaDocument(invoice_id=invoice.id)
        db.add(hacienda_doc)
        await db.flush()
    else:
        hacienda_doc = invoice.hacienda_doc
        hacienda_doc.send_attempts = hacienda_doc.send_attempts + 1

    # Change status to processing
    invoice.status = "processing"
    await db.commit()

    # Queue background task (Celery / asyncio)
    background_tasks.add_task(
        process_invoice_to_hacienda,
        invoice_id=str(invoice_id),
    )

    return HaciendaStatusResponse(
        invoice_id=invoice.id,
        status=invoice.status,
        hacienda_status=hacienda_doc.hacienda_status,
        hacienda_msg="Factura en procesamiento. Consulte el estado en unos momentos.",
        submission_date=hacienda_doc.submission_date,
        response_date=hacienda_doc.response_date,
        send_attempts=hacienda_doc.send_attempts,
        pdf_url=hacienda_doc.pdf_url,
    )


@router.get("/{invoice_id}/status", response_model=HaciendaStatusResponse)
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
@router.post("/{invoice_id}/status/refresh", response_model=HaciendaStatusResponse)
async def refresh_hacienda_status(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Forzar una consulta de estado en tiempo real ante Hacienda y actualizar la DB.
    Este endpoint es consumido por el worker de fondo para sincronización masiva.
    """
    from services.hacienda_service import refresh_invoice_status
    
    status_data = await refresh_invoice_status(
        invoice_id=str(invoice_id),
        db=db,
    )
    
    return HaciendaStatusResponse(**status_data)
