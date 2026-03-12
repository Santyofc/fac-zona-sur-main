"""
utils/base64_encoder.py — Codificación Base64 para Hacienda CR

Hacienda requiere que el XML firmado sea enviado codificado en Base64.
Este módulo provee las funciones de encode/decode con manejo de errores.
"""

from __future__ import annotations

import base64
import logging

logger = logging.getLogger(__name__)


def xml_to_base64(xml_string: str) -> str:
    """
    Codifica un string XML en Base64 para envío a la API de Hacienda.

    Args:
        xml_string: El XML firmado como string (encoding UTF-8).

    Returns:
        String Base64 del XML — compatible con el campo 'comprobanteXml' de Hacienda.

    Example:
        >>> xml_b64 = xml_to_base64(signed_xml)
        >>> payload = {"comprobanteXml": xml_b64, ...}
    """
    if not xml_string:
        raise ValueError("xml_string no puede estar vacío")

    xml_bytes = xml_string.encode("utf-8")
    b64_bytes = base64.b64encode(xml_bytes)
    result    = b64_bytes.decode("ascii")  # Base64 siempre es ASCII

    logger.debug(f"[base64_encoder] XML encodificado: {len(xml_bytes)} bytes → {len(result)} chars B64")
    return result


def base64_to_xml(b64_string: str) -> str:
    """
    Decodifica un string Base64 de vuelta a XML.

    Útil para procesar la respuesta XML de Hacienda (campo 'respuesta-xml').

    Args:
        b64_string: String Base64 recibido de Hacienda.

    Returns:
        XML string decodificado.

    Raises:
        ValueError: Si la cadena no es Base64 válida.
    """
    if not b64_string:
        raise ValueError("b64_string no puede estar vacío")

    try:
        # Limpiar whitespace que Hacienda a veces incluye
        b64_clean = b64_string.strip().replace("\n", "").replace("\r", "")
        xml_bytes = base64.b64decode(b64_clean.encode("ascii"))
        result    = xml_bytes.decode("utf-8")
        logger.debug(f"[base64_encoder] B64 decodificado: {len(b64_clean)} chars → {len(result)} bytes")
        return result
    except Exception as exc:
        raise ValueError(f"No se pudo decodificar Base64: {exc}") from exc


def is_valid_base64(s: str) -> bool:
    """
    Verifica si un string es Base64 válido.

    Returns:
        True si es Base64 válido, False en caso contrario.
    """
    try:
        cleaned = s.strip().replace("\n", "").replace("\r", "")
        base64.b64decode(cleaned, validate=True)
        return True
    except Exception:
        return False
