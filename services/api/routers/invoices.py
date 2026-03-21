"""
Invoices Router — Creación y consulta de facturas electrónicas
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from decimal import Decimal
from datetime import datetime, timedelta

from database import get_db
from config import get_settings
from models.models import User, Invoice, InvoiceItem, Client, Company
from schemas.schemas import InvoiceCreate, InvoiceResponse, InvoiceListItem, DashboardStats
from routers.deps import get_current_user
from services.hacienda.clave import generate_clave, DocType as HaciendaDocType
from services.invoice_hacienda_service import InvoiceHaciendaService

router = APIRouter()

DOC_TYPE_MAP = {
    "FE": HaciendaDocType.FACTURA_ELECTRONICA,
    "TE": HaciendaDocType.TIQUETE_ELECTRONICO,
    "NC": HaciendaDocType.NOTA_CREDITO,
    "ND": HaciendaDocType.NOTA_DEBITO,
}


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Estadísticas del dashboard para la empresa actual."""
    now = datetime.utcnow()
    first_of_month = now.replace(day=1, hour=0, minute=0, second=0)

    # Revenue del mes (facturas aceptadas)
    revenue_q = await db.execute(
        select(func.coalesce(func.sum(Invoice.total), 0)).where(
            Invoice.company_id == current_user.company_id,
            Invoice.status == "accepted",
            Invoice.issue_date >= first_of_month,
        )
    )
    revenue_month = revenue_q.scalar()

    # Contadores por status
    counts_q = await db.execute(
        select(Invoice.status, func.count(Invoice.id)).where(
            Invoice.company_id == current_user.company_id
        ).group_by(Invoice.status)
    )
    counts = {row[0]: row[1] for row in counts_q.all()}

    # IVA acumulado del mes
    tax_q = await db.execute(
        select(func.coalesce(func.sum(Invoice.tax_total), 0)).where(
            Invoice.company_id == current_user.company_id,
            Invoice.status.in_(["accepted", "sent"]),
            Invoice.issue_date >= first_of_month,
        )
    )
    tax_accumulated = tax_q.scalar()

    # Revenue history (últimas 4 semanas)
    revenue_history = []
    for i in range(3, -1, -1):
        start_date = now - timedelta(days=(i+1)*7)
        end_date   = now - timedelta(days=i*7)
        
        hist_q = await db.execute(
            select(func.coalesce(func.sum(Invoice.total), 0)).where(
                Invoice.company_id == current_user.company_id,
                Invoice.status == "accepted",
                Invoice.issue_date >= start_date,
                Invoice.issue_date < end_date,
            )
        )
        val = hist_q.scalar()
        label = f"Sem {4-i}"
        revenue_history.append({"label": label, "value": Decimal(str(val))})

    return DashboardStats(
        revenue_month=Decimal(str(revenue_month)),
        invoices_issued=sum(counts.values()),
        tax_accumulated=Decimal(str(tax_accumulated)),
        invoices_pending=counts.get("processing", 0) + counts.get("sent", 0),
        invoices_accepted=counts.get("accepted", 0),
        invoices_rejected=counts.get("rejected", 0),
        revenue_history=revenue_history,
    )


@router.get("", response_model=List[InvoiceListItem])
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar facturas de la empresa."""
    query = (
        select(Invoice, Client.name.label("client_name"))
        .outerjoin(Client, Invoice.client_id == Client.id)
        .where(Invoice.company_id == current_user.company_id)
    )
    if status_filter:
        query = query.where(Invoice.status == status_filter)
    query = query.offset(skip).limit(limit).order_by(Invoice.issue_date.desc())

    result = await db.execute(query)
    rows = result.all()

    invoices = []
    for invoice, client_name in rows:
        item = InvoiceListItem(
            id=invoice.id,
            consecutive=invoice.consecutive,
            clave=invoice.clave,
            doc_type=invoice.doc_type,
            issue_date=invoice.issue_date,
            total=invoice.total,
            currency=invoice.currency,
            status=invoice.status,
            client_name=client_name,
            created_at=invoice.created_at,
        )
        invoices.append(item)
    return invoices


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Crear una nueva factura electrónica."""
    # Fetch company with SELECT FOR UPDATE to prevent concurrency issues with consecutive_num
    company_result = await db.execute(
        select(Company)
        .where(Company.id == current_user.company_id)
        .with_for_update()
    )
    company = company_result.scalar_one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada.")

    # Convert schema DocType to HaciendaDocType
    hacienda_doc_type = DOC_TYPE_MAP.get(data.doc_type.value, HaciendaDocType.FACTURA_ELECTRONICA)

    # Generate consecutive and clave using the correct logic from clave.py
    clave, consecutive = generate_clave(
        cedula=company.cedula_number,
        sequence_number=company.consecutive_num,
        doc_type=hacienda_doc_type,
    )

    # Calculate totals from items
    subtotal = Decimal("0")
    tax_total = Decimal("0")
    discount_total = Decimal("0")

    invoice = Invoice(
        company_id=current_user.company_id,
        client_id=data.client_id,
        created_by=current_user.id,
        consecutive=consecutive,
        clave=clave,
        doc_type=data.doc_type.value,
        issue_date=data.issue_date or datetime.utcnow(),
        due_date=data.due_date,
        currency=data.currency,
        exchange_rate=data.exchange_rate,
        sale_condition=data.sale_condition,
        payment_method=data.payment_method,
        credit_term_days=data.credit_term_days,
        notes=data.notes,
        status="draft",
    )
    db.add(invoice)
    await db.flush()

    # Create invoice items
    for idx, item_data in enumerate(data.items, start=1):
        quantity = item_data.quantity
        unit_price = item_data.unit_price
        discount_pct = item_data.discount_pct or Decimal("0")
        tax_rate = item_data.tax_rate

        line_subtotal = quantity * unit_price
        discount_amount = (line_subtotal * discount_pct / 100).quantize(Decimal("0.00001"))
        taxable_amount = line_subtotal - discount_amount
        tax_amount = (taxable_amount * tax_rate / 100).quantize(Decimal("0.00001"))
        line_total = taxable_amount + tax_amount

        subtotal += taxable_amount
        tax_total += tax_amount
        discount_total += discount_amount

        item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=item_data.product_id,
            line_number=idx,
            cabys_code=item_data.cabys_code,
            description=item_data.description,
            unit_measure=item_data.unit_measure,
            quantity=quantity,
            unit_price=unit_price,
            discount_pct=discount_pct,
            discount_amount=discount_amount,
            subtotal=taxable_amount,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total=line_total,
        )
        db.add(item)

    # Update invoice totals
    invoice.subtotal = subtotal
    invoice.tax_total = tax_total
    invoice.discount_total = discount_total
    invoice.total = subtotal + tax_total

    # Increment company consecutive
    company.consecutive_num += 1

    await db.flush()
    await db.refresh(invoice)

    # Reload with relationships
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items), selectinload(Invoice.client))
        .where(Invoice.id == invoice.id)
    )
    return result.scalar_one()


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Obtener detalle de una factura."""
    result = await db.execute(
        select(Invoice)
        .options(selectinload(Invoice.items), selectinload(Invoice.client))
        .where(Invoice.id == invoice_id, Invoice.company_id == current_user.company_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")
    return invoice


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Inicia el envío de una factura a Hacienda en segundo plano.
    """
    # Verificar ownership
    result = await db.execute(
        select(Invoice).where(Invoice.id == invoice_id, Invoice.company_id == current_user.company_id)
    )
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada.")

    if invoice.status in ("accepted", "processing"):
        raise HTTPException(status_code=400, detail="La factura ya está en proceso o fue aceptada.")

    # Disparar tarea Celery
    from tasks import send_invoice_to_hacienda
    send_invoice_to_hacienda.delay(str(invoice_id))

    # Actualizar estado local a 'sent' (o 'processing')
    invoice.status = "sent"
    await db.commit()

    return {"message": "Envío iniciado", "invoice_id": invoice_id}


@router.get("/{invoice_id}/status")
async def get_invoice_hacienda_status(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Sincroniza y retorna el estado actual de la factura en Hacienda.
    """
    settings = get_settings()
    service = InvoiceHaciendaService(db, settings)
    
    try:
        # Primero intentamos sincronizar con Hacienda si está pendiente
        result = await service.check_status(str(invoice_id))
        return result
    except Exception as e:
        logger.error(f"Error checking status for {invoice_id}: {e}")
        # Si falla el sync, al menos devolvemos lo que tenemos en DB
        invoice_result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id, Invoice.company_id == current_user.company_id)
        )
        invoice = invoice_result.scalar_one_or_none()
        if not invoice:
            raise HTTPException(status_code=404, detail="Factura no encontrada.")
        
        return {
            "invoice_id": invoice_id,
            "status": invoice.status,
            "message": "No se pudo sincronizar con Hacienda en este momento."
        }
