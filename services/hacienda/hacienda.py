"""
Orquestador Principal — Pipeline de Facturación Electrónica Hacienda CR
Une todos los servicios: generación XML v4.4, firma digital, envío y consulta.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from services.hacienda.clave import generate_clave, DocType, Situation
from services.hacienda.xml_generator import generate_xml
from services.hacienda.signer import sign_xml, xml_to_base64
from services.hacienda.api_client import HaciendaClient, HaciendaAPIError

logger = logging.getLogger(__name__)

# Offset de Costa Rica (CST = UTC-6)
CR_TZ = timezone(timedelta(hours=-6))


def _get_cr_now() -> datetime:
    return datetime.now(CR_TZ)


def _iso_fecha(dt: datetime) -> str:
    """Formatea fecha según ISO 8601 con offset de Costa Rica: 2024-01-15T10:30:00-06:00"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "-06:00"


def build_hacienda_client(config) -> HaciendaClient:
    """
    Construye un cliente de Hacienda a partir de la configuración del sistema.
    """
    return HaciendaClient(
        username    = config.HACIENDA_USERNAME,
        password    = config.HACIENDA_PASSWORD,
        environment = getattr(config, "HACIENDA_ENV", "sandbox"),
    )


async def process_invoice(
    invoice_data: dict,
    company_data: dict,
    config,
    db_session=None,
) -> dict:
    """
    Pipeline completo para procesar una factura electrónica.

    Flujo:
    1. Generar número consecutivo y clave de 50 dígitos
    2. Construir payload del XML
    3. Generar XML v4.4
    4. Firmar digitalmente (XAdES-BES) con certificado BCCR
    5. Convertir a Base64
    6. Enviar a Hacienda
    7. Guardar resultados en la clave retornada

    Args:
        invoice_data: Datos completos de la factura (incluyendo items)
        company_data: Datos de la empresa emisora
        config: Configuración del sistema (settings)
        db_session: Sesión de base de datos (para actualizar estado)

    Returns:
        Dict con resultado del procesamiento: {clave, consecutive, xml, xml_b64, hacienda_result}
    """
    now = _get_cr_now()

    # ─── 1. Clave y Consecutivo ────────────────────────────────────────────────
    doc_type_map = {"FE": DocType.FACTURA_ELECTRONICA, "ND": DocType.NOTA_DEBITO,
                    "NC": DocType.NOTA_CREDITO, "TE": DocType.TIQUETE_ELECTRONICO}
    doc_type = doc_type_map.get(invoice_data.get("doc_type", "FE"), DocType.FACTURA_ELECTRONICA)

    cedula          = "".join(filter(str.isdigit, company_data["cedula_number"]))
    sequence_number = invoice_data.get("sequence_number", 1)

    clave, consecutive = generate_clave(
        cedula          = cedula,
        cedula_type     = company_data.get("cedula_type", "JURIDICA"),
        sequence_number = sequence_number,
        doc_type        = doc_type,
        emission_date   = now,
        situation       = Situation.NORMAL,
    )

    fecha_emision = _iso_fecha(now)
    logger.info(f"📋 Clave generada: {clave} | Consecutivo: {consecutive}")

    # ─── 2. Construir payload XML ──────────────────────────────────────────────
    xml_payload = {
        "doc_type":         invoice_data.get("doc_type", "FE"),
        "clave":            clave,
        "consecutivo":      consecutive,
        "fecha_emision":    fecha_emision,
        "codigo_actividad": company_data.get("actividad_economica", "722000"),
        "emisor": {
            "nombre":        company_data["name"],
            "nombre_comercial": company_data.get("trade_name"),
            "tipo_cedula":   company_data.get("cedula_type", "JURIDICA"),
            "cedula":        cedula,
            "correo":        company_data["email"],
            "telefono":      company_data.get("phone"),
            "ubicacion":     company_data.get("ubicacion"),
        },
        "receptor":         _build_receptor(invoice_data.get("receptor") or invoice_data.get("client")),
        "condicion_venta":  invoice_data.get("sale_condition", "01"),
        "plazo_credito":    invoice_data.get("credit_term_days") if invoice_data.get("sale_condition") == "02" else None,
        "medio_pago":       [invoice_data.get("payment_method", "01")],
        "moneda":           invoice_data.get("currency", "CRC"),
        "tipo_cambio":      float(invoice_data.get("exchange_rate", 1.0)),
        "items":            _build_items(invoice_data.get("items", [])),
        "informacion_referencia": invoice_data.get("referencias", []),
        "otros":            invoice_data.get("notes"),
    }

    # ─── 3. Generar XML v4.4 ─────────────────────────────────────────────────
    xml_str = generate_xml(xml_payload)
    logger.info(f"📄 XML v4.4 generado ({len(xml_str)} bytes)")

    # ─── 4. Firmar ───────────────────────────────────────────────────────────
    p12_path     = getattr(config, "BCCR_P12_PATH", None)
    p12_password = getattr(config, "BCCR_P12_PASSWORD", None)

    signed_xml = sign_xml(xml_str, p12_path, p12_password)
    logger.info(f"✍️  XML firmado ({len(signed_xml)} bytes)")

    # ─── 5. Base64 ───────────────────────────────────────────────────────────
    xml_b64 = xml_to_base64(signed_xml)

    # ─── 6. Preparar respuesta preliminar ────────────────────────────────────
    result = {
        "clave":       clave,
        "consecutive": consecutive,
        "fecha_emision": fecha_emision,
        "xml":         signed_xml,
        "xml_b64":     xml_b64,
        "hacienda_result": None,
    }

    # ─── 7. Enviar a Hacienda ─────────────────────────────────────────────────
    username = getattr(config, "HACIENDA_USERNAME", None)
    password = getattr(config, "HACIENDA_PASSWORD", None)

    if not username or not password:
        logger.warning("⚠️  HACIENDA_USERNAME/PASSWORD no configurados. Omitiendo envío real.")
        result["hacienda_result"] = {
            "hacienda_status": "sandbox_no_sent",
            "message": "Credenciales de Hacienda no configuradas. Modo sandbox local.",
        }
        return result

    try:
        client = build_hacienda_client(config)
        hacienda_result = await client.send_comprobante(
            clave             = clave,
            fecha_emision     = fecha_emision,
            emisor_tipo       = _tipo_code(company_data.get("cedula_type", "JURIDICA")),
            emisor_cedula     = cedula,
            receptor_tipo     = _tipo_code(invoice_data.get("receptor_tipo") or
                                          (invoice_data.get("client", {}) or {}).get("cedula_type", "FISICA")),
            receptor_cedula   = (invoice_data.get("receptor") or invoice_data.get("client", {}) or {}).get("cedula"),
            tipo_comprobante  = invoice_data.get("doc_type", "FE"),
            xml_b64           = xml_b64,
        )
        result["hacienda_result"] = hacienda_result
        logger.info(f"✅ Comprobante enviado a Hacienda: {hacienda_result}")
    except HaciendaAPIError as e:
        logger.error(f"❌ Error al enviar a Hacienda: {e}")
        result["hacienda_result"] = {
            "hacienda_status": "error",
            "error":           str(e),
            "status_code":     e.status_code,
            "detail":          e.detail,
        }

    return result


# ─── Helpers ─────────────────────────────────────────────────────────────────
def _build_receptor(client: dict | None) -> dict | None:
    if not client:
        return None
    return {
        "nombre":     client.get("name", "Consumidor Final"),
        "cedula":     client.get("cedula_number") or client.get("cedula"),
        "tipo_cedula": client.get("cedula_type", "FISICA"),
        "correo":     client.get("email"),
        "ubicacion":  _build_ubicacion_receptor(client),
    }


def _build_ubicacion_receptor(client: dict) -> dict | None:
    if not client.get("province"):
        return None
    return {
        "provincia":   client.get("province", "1"),
        "canton":      client.get("canton", "01"),
        "distrito":    client.get("district", "01"),
        "otras_senas": client.get("address"),
    }


def _build_items(items: list) -> list:
    """Normaliza los items de la factura al formato del XML generator."""
    normalized = []
    for i, item in enumerate(items, start=1):
        tax_rate         = float(item.get("tax_rate", 13))
        impuesto_codigo  = "01" if tax_rate > 0 else "07"
        impuesto_tarifa_codigo = _tarifa_code(tax_rate)

        normalized.append({
            "linea_numero":           i,
            "cabys_code":             item.get("cabys_code", "9999999999999"),
            "descripcion":            item.get("description", "Producto/Servicio"),
            "cantidad":               float(item.get("quantity", 1)),
            "unidad_medida":          item.get("unit_measure", "Unid"),
            "precio_unitario":        float(item.get("unit_price", 0)),
            "descuento_porcentaje":   float(item.get("discount_pct", 0)),
            "naturaleza_descuento":   item.get("discount_nature", "Descuento comercial"),
            "impuesto_codigo":        impuesto_codigo,
            "impuesto_tarifa_codigo": impuesto_tarifa_codigo,
            "impuesto_tarifa":        tax_rate,
            "detalle":                item.get("description"),
        })
    return normalized


def _tarifa_code(tarifa: float) -> str:
    """
    Mapea el porcentaje de tarifa al código de tarifa de Hacienda.
    Tarifas vigentes:
      0%  → "07" (exento tarifa 0)
      1%  → "01"
      2%  → "02"
      4%  → "03"
      8%  → "04" (tarifa reducida)
      13% → "08" (tarifa general)
    """
    mapping = {0: "07", 1: "01", 2: "02", 4: "03", 8: "04", 13: "08"}
    return mapping.get(int(tarifa), "08")


def _tipo_code(tipo: str) -> str:
    mapping = {"FISICA": "01", "JURIDICA": "02", "DIMEX": "03", "NITE": "04", "EXTRANJERO": "05"}
    return mapping.get(tipo.upper(), "02")
