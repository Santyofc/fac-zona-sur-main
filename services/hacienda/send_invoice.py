"""
send_invoice.py — Envío de Comprobantes Electrónicos a Hacienda CR
Responsabilidad: POST /recepcion con payload compliant con API v1.

API Sandbox:  https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1/recepcion
API Producción: https://api.comprobanteselectronicos.go.cr/recepcion/v1/recepcion

Nota: Hacienda responde 202 (Accepted) cuando recibe el comprobante.
El estado definitivo se consulta con check_status.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from .auth_service import AuthService, AuthenticationError

logger = logging.getLogger(__name__)

# Tipo cédula → código Hacienda
CEDULA_TYPE_MAP = {
    "FISICA":     "01",
    "JURIDICA":   "02",
    "DIMEX":      "03",
    "NITE":       "04",
    "EXTRANJERO": "05",
}

# Tipo comprobante → código Hacienda
DOC_TYPE_MAP = {
    "FE":   "01",
    "ND":   "02",
    "NC":   "03",
    "TE":   "04",
    "CCE":  "05",
    "CPCE": "06",
}

API_URLS = {
    "sandbox":    "https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1",
    "production": "https://api.comprobanteselectronicos.go.cr/recepcion/v1",
}


@dataclass
class InvoiceSendResult:
    """Resultado del envío de un comprobante a Hacienda."""
    success:          bool
    http_status:      int
    hacienda_status:  str   # "procesando", "error", "rechazado"
    message:          str
    clave:            str
    raw_response:     Optional[dict] = None


async def send_invoice(
    *,
    clave:            str,
    fecha_emision:    str,
    emisor_tipo:      str,
    emisor_cedula:    str,
    tipo_comprobante: str,
    xml_b64:          str,
    receptor_tipo:    Optional[str]  = None,
    receptor_cedula:  Optional[str]  = None,
    auth:             AuthService,
    environment:      str = "sandbox",
    timeout:          int = 30,
) -> InvoiceSendResult:
    """
    Envía un comprobante electrónico firmado a la API de Hacienda CR.

    Args:
        clave:            Clave numérica de 50 dígitos
        fecha_emision:    ISO 8601 con offset CR: "2024-01-15T10:30:00-06:00"
        emisor_tipo:      Tipo cédula emisor ("FISICA", "JURIDICA", etc.)
        emisor_cedula:    Número de cédula del emisor
        tipo_comprobante: "FE", "ND", "NC", "TE"
        xml_b64:          XML firmado codificado en Base64 UTF-8
        receptor_tipo:    Tipo cédula del receptor (None para tiquetes)
        receptor_cedula:  Cédula del receptor (None para tiquetes)
        auth:             Instancia del AuthService
        environment:      "sandbox" | "production"
        timeout:          Timeout HTTP en segundos

    Returns:
        InvoiceSendResult con el estado del envío
    """
    api_url = f"{API_URLS.get(environment, API_URLS['sandbox'])}/recepcion"

    payload = _build_payload(
        clave, fecha_emision,
        emisor_tipo, emisor_cedula,
        tipo_comprobante, xml_b64,
        receptor_tipo, receptor_cedula,
    )

    logger.info(f"[send_invoice] 📤 Enviando comprobante {clave[:20]}... a Hacienda [{environment}]")

    for attempt in range(2):  # Max 2 intentos (token refresh en 401)
        headers = await auth.get_auth_header()

        async with httpx.AsyncClient(timeout=timeout) as http:
            try:
                resp = await http.post(api_url, json=payload, headers=headers)
            except httpx.ConnectError as exc:
                logger.error(f"[send_invoice] ❌ ConnectError: {exc}")
                return InvoiceSendResult(
                    success=False, http_status=0, clave=clave,
                    hacienda_status="error",
                    message=f"No se pudo conectar a Hacienda: {exc}",
                )
            except httpx.TimeoutException:
                return InvoiceSendResult(
                    success=False, http_status=0, clave=clave,
                    hacienda_status="error",
                    message="Timeout al enviar comprobante a Hacienda",
                )

        logger.info(f"[send_invoice] HTTP {resp.status_code} | clave={clave[:20]}...")

        # ─── 202 = Recibido y en proceso ─────────────────────────────────────
        if resp.status_code in (200, 202):
            return InvoiceSendResult(
                success=True, http_status=resp.status_code, clave=clave,
                hacienda_status="procesando",
                message="Comprobante recibido. Hacienda lo está procesando.",
                raw_response=_safe_json(resp),
            )

        # ─── 401 = Token expirado → refrescar y reintentar ───────────────────
        if resp.status_code == 401 and attempt == 0:
            logger.warning("[send_invoice] Token rechazado (401). Obteniendo token fresco...")
            auth.invalidate()
            continue

        # ─── 400 = Error de validación del payload ────────────────────────────
        if resp.status_code == 400:
            err = _safe_json(resp)
            msg = err.get("message", err.get("error_description", resp.text[:400]))
            logger.error(f"[send_invoice] ❌ Error 400: {msg}")
            return InvoiceSendResult(
                success=False, http_status=400, clave=clave,
                hacienda_status="rechazado",
                message=f"Hacienda rechazó el comprobante: {msg}",
                raw_response=err,
            )

        # ─── Otros errores ────────────────────────────────────────────────────
        return InvoiceSendResult(
            success=False, http_status=resp.status_code, clave=clave,
            hacienda_status="error",
            message=f"Error inesperado (HTTP {resp.status_code}): {resp.text[:300]}",
        )

    # Si se agotaron los reintentos
    return InvoiceSendResult(
        success=False, http_status=401, clave=clave,
        hacienda_status="error",
        message="Autenticación fallida tras reintento.",
    )


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _build_payload(
    clave, fecha_emision,
    emisor_tipo, emisor_cedula,
    tipo_comprobante, xml_b64,
    receptor_tipo, receptor_cedula,
) -> dict:
    """Construye el payload JSON para POST /recepcion."""
    payload = {
        "clave":   clave,
        "fecha":   fecha_emision,
        "emisor": {
            "tipoIdentificacion":   CEDULA_TYPE_MAP.get(emisor_tipo.upper(), "02"),
            "numeroIdentificacion": "".join(filter(str.isdigit, emisor_cedula)),
        },
        "comprobanteXml": xml_b64,
        "callbackUrl":    "",
    }

    if receptor_tipo and receptor_cedula:
        payload["receptor"] = {
            "tipoIdentificacion":   CEDULA_TYPE_MAP.get(receptor_tipo.upper(), "01"),
            "numeroIdentificacion": "".join(filter(str.isdigit, receptor_cedula)),
        }

    return payload


def _safe_json(resp: httpx.Response) -> dict:
    """Intenta parsear la respuesta como JSON, retorna dict vacío si falla."""
    try:
        return resp.json()
    except Exception:
        return {"raw_text": resp.text[:500]}
