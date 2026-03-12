"""
check_status.py — Consulta de Estado de Comprobantes en Hacienda CR
Responsabilidad: GET /recepcion/{clave} y parsing de la respuesta.

Estados posibles de Hacienda:
  procesando  → En cola, aún no hay respuesta definitiva
  aceptado    → Comprobante válido y aceptado
  rechazado   → Comprobante rechazado (ver detalle)
  error       → Error de comunicación o parseo
"""

from __future__ import annotations

import base64
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx

from .auth_service import AuthService

logger = logging.getLogger(__name__)

API_URLS = {
    "sandbox":    "https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1",
    "production": "https://api.comprobanteselectronicos.go.cr/recepcion/v1",
}


class ComprobanteStatus(str, Enum):
    PROCESANDO  = "procesando"
    ACEPTADO    = "aceptado"
    RECHAZADO   = "rechazado"
    NO_ENCONTRADO = "no_encontrado"
    ERROR       = "error"


@dataclass
class StatusResult:
    """Resultado de la consulta de estado de un comprobante."""
    clave:           str
    status:          ComprobanteStatus
    message:         str
    respuesta_xml:   Optional[str] = None    # XML de respuesta de Hacienda (decodificado)
    respuesta_b64:   Optional[str] = None    # Base64 original de la respuesta
    raw_response:    Optional[dict] = None


async def check_status(
    *,
    clave:       str,
    auth:        AuthService,
    environment: str = "sandbox",
    timeout:     int = 20,
) -> StatusResult:
    """
    Consulta el estado de un comprobante enviado a Hacienda CR.

    Args:
        clave:       Clave numérica de 50 dígitos del comprobante
        auth:        Instancia del AuthService con credenciales ATV
        environment: "sandbox" | "production"
        timeout:     Timeout HTTP en segundos

    Returns:
        StatusResult con el estado actual y, si disponible, el XML de respuesta.
    """
    url = f"{API_URLS.get(environment, API_URLS['sandbox'])}/recepcion/{clave}"
    logger.info(f"[check_status] 🔍 Consultando clave {clave[:20]}... [{environment}]")

    for attempt in range(2):
        headers = await auth.get_auth_header()

        async with httpx.AsyncClient(timeout=timeout) as http:
            try:
                resp = await http.get(url, headers=headers)
            except httpx.ConnectError as exc:
                logger.error(f"[check_status] ❌ ConnectError: {exc}")
                return StatusResult(
                    clave=clave,
                    status=ComprobanteStatus.ERROR,
                    message=f"No se pudo conectar a Hacienda: {exc}",
                )
            except httpx.TimeoutException:
                return StatusResult(
                    clave=clave,
                    status=ComprobanteStatus.ERROR,
                    message="Timeout al consultar estado en Hacienda",
                )

        logger.info(f"[check_status] HTTP {resp.status_code} | clave={clave[:20]}...")

        if resp.status_code == 404:
            return StatusResult(
                clave=clave,
                status=ComprobanteStatus.NO_ENCONTRADO,
                message="Comprobante no encontrado en Hacienda. Es posible que aún no haya sido procesado.",
            )

        if resp.status_code == 401 and attempt == 0:
            logger.warning("[check_status] Token rechazado, refrescando...")
            auth.invalidate()
            continue

        if resp.status_code != 200:
            return StatusResult(
                clave=clave,
                status=ComprobanteStatus.ERROR,
                message=f"Error inesperado de Hacienda (HTTP {resp.status_code}): {resp.text[:300]}",
            )

        return _parse_response(clave, resp)

    return StatusResult(
        clave=clave, status=ComprobanteStatus.ERROR,
        message="Autenticación fallida tras reintento.",
    )


def _parse_response(clave: str, resp: httpx.Response) -> StatusResult:
    """
    Parsea la respuesta JSON de Hacienda y mapea el estado.

    Campos esperados en la respuesta de Hacienda:
      ind-estado: "aceptado" | "rechazado" | "procesando"
      respuesta-xml: Base64 del mensaje XML de respuesta
      detalle: descripción del estado
    """
    try:
        data = resp.json()
    except Exception:
        return StatusResult(
            clave=clave,
            status=ComprobanteStatus.ERROR,
            message=f"No se pudo parsear la respuesta de Hacienda: {resp.text[:300]}",
            raw_response=None,
        )

    ind_estado   = data.get("ind-estado", "").lower()
    detalle      = data.get("detalle", data.get("mensaje", ""))
    respuesta_b64 = data.get("respuesta-xml")

    # Decodificar XML de respuesta si está disponible
    respuesta_xml = None
    if respuesta_b64:
        try:
            respuesta_xml = base64.b64decode(respuesta_b64.encode()).decode("utf-8")
        except Exception:
            respuesta_xml = None

    # Mapear ind-estado → ComprobanteStatus
    status_map = {
        "aceptado":    ComprobanteStatus.ACEPTADO,
        "rechazado":   ComprobanteStatus.RECHAZADO,
        "procesando":  ComprobanteStatus.PROCESANDO,
        "recibido":    ComprobanteStatus.PROCESANDO,
        "":            ComprobanteStatus.PROCESANDO,
    }
    status = status_map.get(ind_estado, ComprobanteStatus.PROCESANDO)

    # Generar mensaje legible
    message_prefix = {
        ComprobanteStatus.ACEPTADO:  "✅ Comprobante aceptado por Hacienda",
        ComprobanteStatus.RECHAZADO: "❌ Comprobante RECHAZADO por Hacienda",
        ComprobanteStatus.PROCESANDO:"⏳ Comprobante en procesamiento",
    }.get(status, "Estado desconocido")

    message = f"{message_prefix}: {detalle}" if detalle else message_prefix

    if status == ComprobanteStatus.RECHAZADO:
        logger.warning(f"[check_status] ⚠️  Comprobante rechazado: {detalle}")
    elif status == ComprobanteStatus.ACEPTADO:
        logger.info(f"[check_status] ✅ Comprobante aceptado")

    return StatusResult(
        clave=clave,
        status=status,
        message=message,
        respuesta_xml=respuesta_xml,
        respuesta_b64=respuesta_b64,
        raw_response=data,
    )
