"""
Sender Service — Envía el XML firmado a la API de Hacienda CR (ATV / comprobantes electrónicos).
Implementa OAuth2 Client Credentials para obtener el token de Hacienda.
"""
import httpx
import base64
import logging
from datetime import datetime
from config import settings

logger = logging.getLogger(__name__)

# Cache simple del token (en producción usar Redis)
_token_cache = {"token": None, "expires_at": None}


async def _get_hacienda_token(hacienda_user: str = None, hacienda_pass: str = None) -> str:
    """Obtene un token OAuth2 de Hacienda CR."""
    now = datetime.utcnow()
    if _token_cache["token"] and _token_cache["expires_at"] and _token_cache["expires_at"] > now.timestamp():
        return _token_cache["token"]

    username = hacienda_user or settings.HACIENDA_USERNAME
    password = hacienda_pass or settings.HACIENDA_PASSWORD

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            settings.HACIENDA_TOKEN_URL,
            data={
                "grant_type": "password",
                "client_id": settings.HACIENDA_CLIENT_ID,
                "client_secret": settings.HACIENDA_CLIENT_SECRET,
                "username": username,
                "password": password,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        data = response.json()
        _token_cache["token"] = data["access_token"]
        _token_cache["expires_at"] = now.timestamp() + data.get("expires_in", 300) - 30
        return _token_cache["token"]


async def send_to_hacienda_api(
    clave: str,
    xml_signed: str,
    cedula_emisor: str,
    cedula_type: str = "JURIDICA",
    hacienda_user: str = None,
    hacienda_pass: str = None,
) -> dict:
    """
    Envía el XML firmado a la API de Hacienda CR.

    Endpoint: POST /recepcion/v1/recepcion
    Body: JSON con el XML encodado en base64

    Returns:
        dict con estado y mensaje de Hacienda
    """
    if not settings.HACIENDA_CLIENT_ID:
        # Modo sandbox sin credenciales — simular respuesta exitosa
        logger.warning("[Sender] Sin credenciales Hacienda. Simulando envío exitoso (sandbox).")
        return {
            "estado": "procesando",
            "mensaje": "Comprobante recibido para procesamiento (modo sandbox)",
        }

    try:
        token = await _get_hacienda_token(hacienda_user, hacienda_pass)
        xml_b64 = base64.b64encode(xml_signed.encode("utf-8")).decode("utf-8")

        cedula_digits = "".join(filter(str.isdigit, cedula_emisor))
        cedula_code = {"FISICA": "01", "JURIDICA": "02", "DIMEX": "03", "NITE": "04"}.get(cedula_type, "02")

        payload = {
            "clave": clave,
            "fecha": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S-06:00"),
            "emisor": {
                "tipoIdentificacion": cedula_code,
                "numeroIdentificacion": cedula_digits,
            },
            "comprobanteXml": xml_b64,
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{settings.HACIENDA_API_URL}/recepcion",
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )

            if response.status_code == 202:
                return {"estado": "procesando", "mensaje": "Comprobante recibido exitosamente"}
            elif response.status_code == 400:
                error_data = response.json()
                return {"estado": "rechazado", "mensaje": error_data.get("detalle", "Error de validación")}
            else:
                response.raise_for_status()
                return {"estado": "procesando", "mensaje": "Enviado"}

    except httpx.HTTPStatusError as e:
        logger.error(f"[Sender] HTTP Error: {e.response.status_code} — {e.response.text}")
        raise
    except Exception as e:
        logger.error(f"[Sender] Error enviando a Hacienda: {e}")
        raise
