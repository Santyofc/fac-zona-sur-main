"""
xml/factura_xml.py — Facade del Generador de XML v4.4 para Hacienda CR

Punto de entrada principal para generación de XML de comprobantes.
Delega al xml_generator.py del engine central.

Tipos de comprobante soportados:
  FE — FacturaElectronica
  ND — NotaDebitoElectronica
  NC — NotaCreditoElectronica
  TE — TiqueteElectronico
"""

from __future__ import annotations

import logging
from typing import Optional

# Importar el generador central
from services.hacienda.xml_generator import generate_xml, _calculate_totals

logger = logging.getLogger(__name__)


def build_factura_electronica(payload: dict) -> str:
    """
    Genera el XML de una Factura Electrónica (FE).

    Args:
        payload: Diccionario con los datos de la factura. Estructura mínima:
            {
              "clave":          str,   # 50 dígitos
              "consecutivo":    str,   # 20 dígitos
              "fecha_emision":  str,   # ISO 8601 con offset -06:00
              "emisor":         dict,  # {nombre, cedula, tipo_cedula, correo}
              "receptor":       dict,  # {nombre, cedula, tipo_cedula, correo}
              "condicion_venta": str,  # "01" = Contado
              "medio_pago":     list,  # ["01"] = Efectivo
              "items":          list,  # Lista de líneas de detalle
            }

    Returns:
        XML string formateado, UTF-8.
    """
    _payload = {**payload, "doc_type": "FE"}
    logger.info(f"[build_factura_electronica] Generando XML FE | clave={payload.get('clave', '?')[:20]}...")
    xml = generate_xml(_payload)
    logger.debug(f"[build_factura_electronica] XML generado: {len(xml)} bytes")
    return xml


def build_tiquete_electronico(payload: dict) -> str:
    """
    Genera el XML de un Tiquete Electrónico (TE).
    A diferencia de FE, el receptor es opcional (puede ser Consumidor Final).
    """
    _payload = {**payload, "doc_type": "TE", "receptor": None}
    logger.info(f"[build_tiquete_electronico] Generando XML TE | clave={payload.get('clave', '?')[:20]}...")
    return generate_xml(_payload)


def build_nota_credito(payload: dict, referencias: list[dict]) -> str:
    """
    Genera el XML de una Nota de Crédito Electrónica (NC).

    Args:
        payload: Datos del comprobante base
        referencias: Lista de referencias a facturas que se anulan/modifican.
            Cada referencia: {tipo_doc, numero, fecha_emision, codigo, razon}
            Códigos:
              01 = Anula documento de referencia
              02 = Corrige texto documento de referencia
              03 = Corrige monto
              04 = Referencia a otro documento
              05 = Sustituye comprobante provisional por CE
              99 = Otros
    """
    _payload = {**payload, "doc_type": "NC", "informacion_referencia": referencias}
    logger.info(f"[build_nota_credito] Generando XML NC | clave={payload.get('clave', '?')[:20]}...")
    return generate_xml(_payload)


def build_nota_debito(payload: dict, referencias: list[dict]) -> str:
    """
    Genera el XML de una Nota de Débito Electrónica (ND).

    Args:
        payload: Datos del comprobante
        referencias: Facturas a las que se agrega débito
    """
    _payload = {**payload, "doc_type": "ND", "informacion_referencia": referencias}
    logger.info(f"[build_nota_debito] Generando XML ND | clave={payload.get('clave', '?')[:20]}...")
    return generate_xml(_payload)


def get_totals(items: list[dict]) -> dict:
    """
    Calcula los totales del resumen de factura sin generar XML.
    Útil para preview en el frontend.

    Returns:
        Dict con total_venta, total_impuesto, total_comprobante, etc.
    """
    return {k: float(v) for k, v in _calculate_totals(items).items()}
