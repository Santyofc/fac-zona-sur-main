"""
Hacienda Service — Capa de orquestación en services/api
Wrapper del engine hacienda/ integrado con la base de datos FastAPI.
"""

from __future__ import annotations

import logging
import sys
import os
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

logger = logging.getLogger(__name__)

# Importar el engine de hacienda (manejar tanto monorepo como ejecución directa)
try:
    from services.hacienda.hacienda import process_invoice as _process_invoice
except ImportError:
    # Fallback: buscar en el directorio hermano
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "hacienda"))
    from hacienda import process_invoice as _process_invoice  # type: ignore


async def process_invoice_to_hacienda(
    invoice_id: str,
    db: AsyncSession,
    config,
) -> dict:
    """
    Orquesta el pipeline completo de una factura con la base de datos.

    1. Carga la factura e items desde la DB
    2. Carga los datos de la empresa
    3. Ejecuta el pipeline Hacienda (XML → firma → envío)
    4. Actualiza la factura y crea HaciendaDocument en la DB

    Returns:
        Dict con resultado del procesamiento
    """
    from models.models import Invoice, InvoiceItem, Company, Client, HaciendaDocument

    # ─── Cargar factura ────────────────────────────────────────────────────────
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise ValueError(f"Factura no encontrada: {invoice_id}")

    # ─── Cargar items ──────────────────────────────────────────────────────────
    items_result = await db.execute(
        select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id).order_by(InvoiceItem.line_number)
    )
    items = items_result.scalars().all()

    # ─── Cargar empresa ────────────────────────────────────────────────────────
    comp_result = await db.execute(select(Company).where(Company.id == invoice.company_id))
    company     = comp_result.scalar_one()

    # ─── Cargar cliente ────────────────────────────────────────────────────────
    client_data = None
    if invoice.client_id:
        cli_result  = await db.execute(select(Client).where(Client.id == invoice.client_id))
        client_obj  = cli_result.scalar_one_or_none()
        if client_obj:
            client_data = {
                "name":         client_obj.name,
                "cedula_number": client_obj.cedula_number,
                "cedula_type":  client_obj.cedula_type,
                "email":        client_obj.email,
                "province":     client_obj.province,
                "canton":       client_obj.canton,
                "district":     client_obj.district,
                "address":      client_obj.address,
            }

    # ─── Obtener número de secuencia actualizado ───────────────────────────────
    company.consecutive_num = (company.consecutive_num or 0) + 1
    sequence_number = company.consecutive_num
    await db.flush()

    # ─── Datos para el pipeline ────────────────────────────────────────────────
    invoice_data = {
        "doc_type":        invoice.doc_type or "FE",
        "sequence_number": sequence_number,
        "currency":        invoice.currency or "CRC",
        "exchange_rate":   float(invoice.exchange_rate or 1.0),
        "sale_condition":  invoice.sale_condition or "01",
        "payment_method":  invoice.payment_method or "01",
        "credit_term_days": invoice.credit_term_days,
        "notes":           invoice.notes,
        "client":          client_data,
        "items": [
            {
                "cabys_code":    item.cabys_code or "9999999999999",
                "description":   item.description,
                "quantity":      float(item.quantity),
                "unit_price":    float(item.unit_price),
                "unit_measure":  item.unit_measure or "Unid",
                "discount_pct":  float(item.discount_pct or 0),
                "tax_rate":      float(item.tax_rate or 13),
            }
            for item in items
        ],
    }

    company_data = {
        "name":               company.name,
        "trade_name":         company.trade_name,
        "cedula_type":        company.cedula_type,
        "cedula_number":      company.cedula_number,
        "email":              company.email,
        "phone":              company.phone,
        "actividad_economica": getattr(company, "actividad_economica", "722000"),
        "ubicacion": {
            "provincia": company.province or "1",
            "canton":    company.canton or "01",
            "distrito":  company.district or "01",
            "otras_senas": company.address,
        },
    }

    # ─── Ejecutar pipeline ────────────────────────────────────────────────────
    logger.info(f"🚀 Iniciando pipeline Hacienda para factura {invoice_id}")
    pipeline_result = await _process_invoice(invoice_data, company_data, config)

    clave       = pipeline_result["clave"]
    consecutive = pipeline_result["consecutive"]
    signed_xml  = pipeline_result["xml"]
    hacienda_r  = pipeline_result.get("hacienda_result", {})

    # ─── Actualizar factura ───────────────────────────────────────────────────
    invoice.clave             = clave
    invoice.consecutive       = consecutive
    invoice.issue_date        = datetime.now(timezone(timedelta(hours=-6)))
    invoice.status            = "processing" if hacienda_r.get("success") else "sent"

    # ─── Crear/actualizar HaciendaDocument ───────────────────────────────────
    hac_result = await db.execute(
        select(HaciendaDocument).where(HaciendaDocument.invoice_id == invoice_id)
    )
    hac_doc = hac_result.scalar_one_or_none()

    if not hac_doc:
        from uuid import uuid4
        hac_doc = HaciendaDocument(id=str(uuid4()), invoice_id=invoice_id)
        db.add(hac_doc)

    hac_doc.xml_filename      = f"{clave}.xml"
    hac_doc.submission_date   = datetime.now(timezone.utc)
    hac_doc.hacienda_status   = hacienda_r.get("hacienda_status", "procesando")
    hac_doc.hacienda_msg      = hacienda_r.get("message", "")
    hac_doc.send_attempts     = (hac_doc.send_attempts or 0) + 1
    hac_doc.last_attempt_at   = datetime.now(timezone.utc)

    # ─── Guardar XML en Supabase Storage (placeholder) ───────────────────────
    # TODO: subir signed_xml a Supabase Storage y guardar URL en hac_doc.pdf_url

    await db.commit()
    logger.info(f"✅ Procesamiento completado: {invoice_id} → {clave}")

    return {
        "invoice_id": invoice_id,
        "clave":      clave,
        "consecutive": consecutive,
        "status":     hac_doc.hacienda_status,
        "hacienda":   hacienda_r,
    }
