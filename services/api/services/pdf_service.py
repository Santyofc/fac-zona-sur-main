"""
PDF Service — Genera facturas en PDF con QR Code
Usa ReportLab para el layout y qrcode para el código QR.
"""

from __future__ import annotations

import io
import os
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional

logger = logging.getLogger(__name__)


def _safe_decimal(value) -> Decimal:
    try:
        return Decimal(str(value or 0))
    except Exception:
        return Decimal("0")


def generate_invoice_pdf(invoice_data: dict) -> bytes:
    """
    Genera el PDF de una factura electrónica.

    Args:
        invoice_data: Diccionario con datos de la factura. Campos:
          - company: {name, cedula_number, email, phone, address, logo_url?}
          - client: {name, cedula_number, email, address}
          - consecutive: str
          - clave: str
          - issue_date: datetime | str
          - currency: str
          - items: list[{description, quantity, unit_price, tax_rate, total}]
          - subtotal, tax_total, total
          - notes: str

    Returns:
        Bytes del PDF generado
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm, cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer,
            Table, TableStyle, Image, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    except ImportError:
        raise ImportError("ReportLab no instalado. Ejecutar: pip install reportlab")

    # ─── Buffer en memoria ────────────────────────────────────────────────────
    buffer = io.BytesIO()

    # ─── Config página ────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )

    # ─── Estilos ──────────────────────────────────────────────────────────────
    styles   = getSampleStyleSheet()
    dark     = colors.HexColor("#0D1B2E")
    blue     = colors.HexColor("#2563EB")
    light    = colors.HexColor("#F1F5F9")
    muted    = colors.HexColor("#64748B")
    success  = colors.HexColor("#10B981")
    white    = colors.white

    title_style = ParagraphStyle("Title", parent=styles["Heading1"],
                                  fontSize=20, textColor=dark, spaceAfter=4, leading=24)
    h2_style    = ParagraphStyle("H2",    parent=styles["Heading2"],
                                  fontSize=11, textColor=dark, spaceAfter=4, leading=14)
    body_style  = ParagraphStyle("Body",  parent=styles["Normal"],
                                  fontSize=9, textColor=dark, leading=13)
    small_style = ParagraphStyle("Small", parent=styles["Normal"],
                                  fontSize=8, textColor=muted, leading=11)
    right_style = ParagraphStyle("Right", parent=styles["Normal"],
                                  fontSize=9, textColor=dark, alignment=TA_RIGHT)

    # ─── Formatear moneda ──────────────────────────────────────────────────────
    currency    = invoice_data.get("currency", "CRC")
    locale_code = "es-CR"
    def fmt(v):
        try:
            num = float(_safe_decimal(v))
            symbol = "₡" if currency == "CRC" else "$"
            return f"{symbol}{num:,.0f}" if currency == "CRC" else f"{symbol}{num:,.2f}"
        except Exception:
            return "—"

    # ─── Datos ────────────────────────────────────────────────────────────────
    company     = invoice_data.get("company", {})
    client      = invoice_data.get("client") or {}
    items       = invoice_data.get("items", [])
    consecutive = invoice_data.get("consecutive", "")
    clave       = invoice_data.get("clave", "")
    issue_date  = invoice_data.get("issue_date", datetime.now())
    if isinstance(issue_date, str):
        try:
            issue_date = datetime.fromisoformat(issue_date.replace("Z", "+00:00"))
        except Exception:
            issue_date = datetime.now()

    formatted_date = issue_date.strftime("%d/%m/%Y %H:%M")

    # ─── Construir QR ─────────────────────────────────────────────────────────
    qr_image = _generate_qr_image(clave) if clave else None

    # ─── Elementos del documento ──────────────────────────────────────────────
    story = []

    # Encabezado: Logo, nombre empresa, info comprobante
    header_data = [
        [
            Paragraph(f"<b>{company.get('name', 'Empresa SRL')}</b>", title_style),
            Paragraph(
                f"<b>FACTURA ELECTRÓNICA</b><br/>"
                f"Consecutivo: {consecutive}<br/>"
                f"Fecha: {formatted_date}",
                ParagraphStyle("HeaderRight", parent=body_style, alignment=TA_RIGHT, fontSize=10)
            ),
        ]
    ]
    header_table = Table(header_data, colWidths=["60%", "40%"])
    header_table.setStyle(TableStyle([
        ("ALIGN",     (0, 0), (0, 0), "LEFT"),
        ("ALIGN",     (1, 0), (1, 0), "RIGHT"),
        ("VALIGN",    (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4*mm))

    # Empresa info
    story.append(Paragraph(
        f"Cédula: {company.get('cedula_number', '')} | "
        f"Email: {company.get('email', '')} | "
        f"Tel: {company.get('phone', '')}",
        small_style
    ))
    if addr := company.get("address"):
        story.append(Paragraph(f"Dirección: {addr}", small_style))
    story.append(HRFlowable(width="100%", thickness=2, color=blue, spaceAfter=6, spaceBefore=6))

    # Info emisión + cliente
    issue_data = [
        [
            Table(
                [[Paragraph("<b>DATOS DEL RECEPTOR</b>", small_style)],
                 [Paragraph(f"Nombre: <b>{client.get('name', 'Consumidor Final')}</b>", body_style)],
                 [Paragraph(f"Cédula: {client.get('cedula_number', 'N/A')}", body_style)],
                 [Paragraph(f"Email: {client.get('email', '')}", body_style)],
                 [Paragraph(f"Dirección: {client.get('address', '')}", body_style)]],
                colWidths=["100%"]
            ),
            Table(
                [[Paragraph("<b>DETALLES</b>", small_style)],
                 [Paragraph(f"Moneda: <b>{currency}</b>", body_style)],
                 [Paragraph(f"Condición: Contado", body_style)],
                 [Paragraph(f"Tipo: Factura Electrónica", body_style)],
                 [qr_image if qr_image else Paragraph("", body_style)]],
                colWidths=["100%"]
            ),
        ]
    ]
    issue_table = Table(issue_data, colWidths=["60%", "40%"])
    issue_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN",  (1, 0), (1, -1), "RIGHT"),
    ]))
    story.append(issue_table)
    story.append(Spacer(1, 5*mm))

    # ─── Tabla de ítems ───────────────────────────────────────────────────────
    item_headers = [
        Paragraph("<b>CABYS</b>", small_style),
        Paragraph("<b>DESCRIPCIÓN</b>", small_style),
        Paragraph("<b>CANT.</b>", small_style),
        Paragraph("<b>PRECIO U.</b>", small_style),
        Paragraph("<b>IVA %</b>", small_style),
        Paragraph("<b>SUBTOTAL</b>", small_style),
    ]

    item_rows = [item_headers]
    alt = False
    for item in items:
        qty    = _safe_decimal(item.get("quantity", 1))
        price  = _safe_decimal(item.get("unit_price", 0))
        tax_r  = _safe_decimal(item.get("tax_rate", 13))
        sub    = qty * price
        item_rows.append([
            Paragraph(str(item.get("cabys_code", ""))[:10], small_style),
            Paragraph(str(item.get("description", ""))[:80], body_style),
            Paragraph(f"{float(qty):,.3f}", right_style),
            Paragraph(fmt(price), right_style),
            Paragraph(f"{float(tax_r):.0f}%", right_style),
            Paragraph(fmt(sub), right_style),
        ])
        alt = not alt

    items_table = Table(item_rows, colWidths=[25*mm, 70*mm, 18*mm, 28*mm, 18*mm, 28*mm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, 0), blue),
        ("TEXTCOLOR",   (0, 0), (-1, 0), white),
        ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",    (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [light, white]),
        ("ALIGN",       (2, 1), (-1, -1), "RIGHT"),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
        ("PADDING",     (0, 0), (-1, -1), 5),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 5*mm))

    # ─── Totales ──────────────────────────────────────────────────────────────
    subtotal   = _safe_decimal(invoice_data.get("subtotal", 0))
    tax_total  = _safe_decimal(invoice_data.get("tax_total", 0))
    discount   = _safe_decimal(invoice_data.get("discount_total", 0))
    total      = _safe_decimal(invoice_data.get("total", 0))

    totals_data = []
    if discount > 0:
        totals_data.append(["Descuentos:", fmt(discount)])
    totals_data += [
        ["Subtotal:",       fmt(subtotal)],
        ["IVA Total:",      fmt(tax_total)],
        ["", ""],
        [Paragraph("<b>TOTAL A PAGAR:</b>", body_style), Paragraph(f"<b>{fmt(total)}</b>", right_style)],
    ]

    totals_table = Table(totals_data, colWidths=["75%", "25%"])
    totals_table.setStyle(TableStyle([
        ("ALIGN",      (1, 0), (1, -1), "RIGHT"),
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("LINEABOVE",  (0, -1), (-1, -1), 1.5, dark),
        ("TOPPADDING", (0, -1), (-1, -1), 6),
        ("PADDING",    (0, 0), (-1, -1), 3),
    ]))
    story.append(totals_table)

    # ─── Footer ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=muted, spaceAfter=4))

    if notes := invoice_data.get("notes"):
        story.append(Paragraph(f"<b>Notas:</b> {notes}", small_style))
        story.append(Spacer(1, 3*mm))

    # Clave completa para verificación
    if clave:
        story.append(Paragraph(
            f"Clave numérica: {clave}",
            ParagraphStyle("Clave", parent=small_style, fontName="Courier", fontSize=7)
        ))
    story.append(Paragraph(
        "Comprobante electrónico emitido según Resolución DGT-R-48-2016 "
        "del Ministerio de Hacienda de Costa Rica.",
        ParagraphStyle("Legal", parent=small_style, textColor=muted)
    ))

    # ─── Build ────────────────────────────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    return buffer.read()


def _generate_qr_image(clave: str, size_mm: int = 25):
    """
    Genera un objeto Image de ReportLab con el QR de la clave.
    El QR contiene la URL de verificación en Hacienda.
    """
    try:
        import qrcode
        from reportlab.lib.units import mm
        from reportlab.platypus import Image as RLImage

        verify_url = f"https://www.hacienda.go.cr/consultahacienda/pages/detalleComprobante.jsf?clave={clave}"
        qr = qrcode.QRCode(version=1, box_size=3, border=1)
        qr.add_data(verify_url)
        qr.make(fit=True)

        img_io = io.BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(img_io, format="PNG")
        img_io.seek(0)

        return RLImage(img_io, width=size_mm*mm, height=size_mm*mm)
    except ImportError:
        logger.warning("qrcode no instalado. Omitiendo QR del PDF.")
        return None
    except Exception as e:
        logger.error(f"Error generando QR: {e}")
        return None
