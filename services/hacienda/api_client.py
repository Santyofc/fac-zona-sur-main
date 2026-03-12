"""
Cliente API — Ministerio de Hacienda CR (Comprobantes Electrónicos)
Implementa el flujo completo de autenticación OAuth2 y envío de comprobantes.

Endpoints:
  Sandbox Recepción: https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1
  Sandbox OAuth IDP: https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token
  Prod Recepción:    https://api.comprobanteselectronicos.go.cr/recepcion/v1
  Prod OAuth IDP:    https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token

Client IDs:
  Sandbox: api-stag
  Prod:    api-prod

Flujo:
  1. POST /token (OAuth2 Resource Owner Password Credentials — ROPC)
  2. POST /recepcion  → enviar comprobante firmado en Base64
  3. GET  /recepcion/{clave} → consultar estado del comprobante
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Configuración de Ambientes ────────────────────────────────────────────────
ENVIRONMENTS = {
    "sandbox": {
        "token_url":   "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token",
        "api_url":     "https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1",
        "client_id":  "api-stag",
    },
    "production": {
        "token_url":   "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token",
        "api_url":     "https://api.comprobanteselectronicos.go.cr/recepcion/v1",
        "client_id":  "api-prod",
    },
}

# Cache de tokens en memoria (por usuario@empresa)
_token_cache: dict[str, dict] = {}


class HaciendaAPIError(Exception):
    """Error retornado por la API de Hacienda."""
    def __init__(self, status_code: int, message: str, detail: dict | None = None):
        self.status_code = status_code
        self.message     = message
        self.detail      = detail or {}
        super().__init__(f"API Hacienda Error {status_code}: {message}")


class HaciendaClient:
    """
    Cliente asincrónico para la API de Hacienda CR.

    Uso:
        client = HaciendaClient(
            username="usuario@atv.hacienda.go.cr",
            password="contraseña_atv",
            environment="sandbox",
        )
        token    = await client.get_token()
        clave_status = await client.get_comprobante_status(clave)
    """

    def __init__(
        self,
        username: str,
        password: str,
        environment: str = "sandbox",
        timeout: int = 30,
    ):
        if environment not in ENVIRONMENTS:
            raise ValueError(f"Ambiente inválido: {environment}. Usar 'sandbox' o 'production'")
        self.username    = username
        self.password    = password
        self.environment = environment
        self.timeout     = timeout
        self._env        = ENVIRONMENTS[environment]

    @property
    def _cache_key(self) -> str:
        return f"{self.username}:{self.environment}"

    async def get_token(self, force_refresh: bool = False) -> str:
        """
        Obtiene el token de acceso OAuth2 de Hacienda.
        Usa caché en memoria para reutilizar tokens válidos.

        Args:
            force_refresh: Si True, obtiene nuevo token aunque el cacheado sea válido.

        Returns:
            access_token como string
        """
        cache = _token_cache.get(self._cache_key)

        # Verificar si el token en caché sigue siendo válido (margen 60 segundos)
        if not force_refresh and cache and cache["expires_at"] > time.time() + 60:
            logger.debug(f"♻️  Token en caché válido para {self.username}")
            return cache["access_token"]

        logger.info(f"🔑 Obteniendo token OAuth2 de Hacienda ({self.environment}) para {self.username}")

        payload = {
            "grant_type":  "password",
            "client_id":   self._env["client_id"],
            "username":    self.username,
            "password":    self.password,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(
                    self._env["token_url"],
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            except httpx.ConnectError as e:
                raise HaciendaAPIError(0, f"No se pudo conectar al IDP de Hacienda: {e}")
            except httpx.TimeoutException:
                raise HaciendaAPIError(0, "Tiempo de espera agotado al obtener token de Hacienda")

        if resp.status_code != 200:
            logger.error(f"❌ Error al obtener token: {resp.status_code} — {resp.text}")
            raise HaciendaAPIError(
                resp.status_code,
                "Error de autenticación con Hacienda",
                {"response": resp.text[:500]},
            )

        data         = resp.json()
        access_token = data["access_token"]
        expires_in   = data.get("expires_in", 300)  # Default 5 minutos

        _token_cache[self._cache_key] = {
            "access_token": access_token,
            "expires_at":   time.time() + expires_in,
        }

        logger.info(f"✅ Token obtenido. Expira en {expires_in}s")
        return access_token

    async def send_comprobante(
        self,
        clave: str,
        fecha_emision: str,
        emisor_tipo: str,
        emisor_cedula: str,
        receptor_tipo: str | None,
        receptor_cedula: str | None,
        tipo_comprobante: str,
        xml_b64: str,
        return_msg: str = "",
    ) -> dict:
        """
        Envía un comprobante electrónico a la API de Hacienda.

        Args:
            clave: Clave de 50 dígitos
            fecha_emision: Fecha en formato ISO 8601 con offset: "2024-01-15T10:30:00-06:00"
            emisor_tipo: Tipo cédula emisor (01, 02, 03, 04)
            emisor_cedula: Número de cédula del emisor
            receptor_tipo: Tipo cédula receptor (None para tiquetes)
            receptor_cedula: Cédula del receptor (None para tiquetes)
            tipo_comprobante: "FE", "ND", "NC", "TE"
            xml_b64: XML firmado codificado en Base64

        Returns:
            Dict con resultado del envío
        """
        token = await self.get_token()

        # Mapeo tipo comprobante
        tipo_codes = {"FE": "01", "ND": "02", "NC": "03", "TE": "04", "CCE": "05", "CPCE": "06"}
        tipo_code = tipo_codes.get(tipo_comprobante, "01")

        payload = {
            "clave":            clave,
            "fecha":            fecha_emision,
            "emisor": {
                "tipoIdentificacion":   emisor_tipo,
                "numeroIdentificacion": "".join(filter(str.isdigit, emisor_cedula)),
            },
            "comprobanteXml":   xml_b64,
            "callbackUrl":      "",
        }

        # Receptor (requerido para FE/ND/NC, opcional para TE)
        if receptor_tipo and receptor_cedula:
            payload["receptor"] = {
                "tipoIdentificacion":   receptor_tipo,
                "numeroIdentificacion": "".join(filter(str.isdigit, receptor_cedula)),
            }

        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(
                    f"{self._env['api_url']}/recepcion",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type":  "application/json",
                    },
                )
            except httpx.ConnectError as e:
                raise HaciendaAPIError(0, f"No se pudo conectar a la API de Hacienda: {e}")
            except httpx.TimeoutException:
                raise HaciendaAPIError(0, "Timeout al enviar comprobante a Hacienda")

        logger.info(f"📤 Comprobante enviado | clave: {clave[:20]}... | HTTP: {resp.status_code}")

        # 202 = Procesando (éxito normal)
        if resp.status_code in (200, 202):
            return {
                "success":     True,
                "status_code": resp.status_code,
                "message":     "Comprobante recibido y en proceso de validación",
                "hacienda_status": "procesando",
            }

        # 400 = Error de validación
        if resp.status_code == 400:
            try:
                err = resp.json()
            except Exception:
                err = {"message": resp.text}
            raise HaciendaAPIError(400, err.get("message", "Error de validación"), err)

        # 401 = Token expirado — retry
        if resp.status_code == 401:
            logger.warning("Token expirado. Reintentando con token fresco...")
            token = await self.get_token(force_refresh=True)
            # Recursive retry (solo una vez)
            return await self.send_comprobante(
                clave, fecha_emision, emisor_tipo, emisor_cedula,
                receptor_tipo, receptor_cedula, tipo_comprobante, xml_b64
            )

        raise HaciendaAPIError(resp.status_code, f"Error inesperado de Hacienda: {resp.text[:200]}")

    async def get_comprobante_status(self, clave: str) -> dict:
        """
        Consulta el estado de un comprobante enviado a Hacienda.

        Args:
            clave: Clave de 50 dígitos del comprobante

        Returns:
            Dict con el estado del comprobante:
            {
              "ind-estado": "aceptado" | "rechazado" | "procesando",
              "respuesta-xml": "...",  # Base64 XML de respuesta (si disponible)
              "raw": {...}             # Respuesta completa de Hacienda
            }
        """
        token = await self.get_token()

        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.get(
                    f"{self._env['api_url']}/recepcion/{clave}",
                    headers={"Authorization": f"Bearer {token}"},
                )
            except httpx.ConnectError as e:
                raise HaciendaAPIError(0, f"No se pudo conectar a la API de Hacienda: {e}")
            except httpx.TimeoutException:
                raise HaciendaAPIError(0, "Timeout al consultar estado en Hacienda")

        logger.info(f"🔍 Estado consultado | clave: {clave[:20]}... | HTTP: {resp.status_code}")

        if resp.status_code == 404:
            return {"ind-estado": "no_encontrado", "raw": {}}

        if resp.status_code == 401:
            token = await self.get_token(force_refresh=True)
            return await self.get_comprobante_status(clave)

        if resp.status_code != 200:
            raise HaciendaAPIError(resp.status_code, f"Error al consultar estado: {resp.text[:200]}")

        try:
            data = resp.json()
        except Exception:
            data = {"ind-estado": "error_parse", "raw_text": resp.text}

        return {
            "hacienda_status": data.get("ind-estado", "procesando"),
            "respuesta_xml":   data.get("respuesta-xml", ""),
            "mensaje":         data.get("detalle", ""),
            "raw":             data,
        }

    async def full_pipeline(
        self,
        xml_str: str,
        xml_b64: str,
        clave: str,
        consecutive: str,
        fecha_emision: str,
        emisor: dict,
        receptor: dict | None,
        tipo_comprobante: str = "FE",
        poll_status: bool = False,
        poll_max_seconds: int = 30,
    ) -> dict:
        """
        Pipeline completo: enviar comprobante y opcionalmente esperar la respuesta.

        Args:
            xml_str: XML original (sin firmar o firmado)
            xml_b64: XML firmado en Base64
            clave: Clave 50 dígitos
            consecutive: Número consecutivo 20 dígitos
            fecha_emision: ISO 8601 con timezone
            emisor: {tipo_cedula, cedula}
            receptor: {tipo_cedula, cedula} o None
            tipo_comprobante: "FE", "ND", "NC", "TE"
            poll_status: Si True, hace polling hasta obtener respuesta
            poll_max_seconds: Tiempo máximo de polling en segundos

        Returns:
            Dict con resultado completo del pipeline
        """
        # Mapeo tipo cédula → código Hacienda
        tipo_map = {"FISICA": "01", "JURIDICA": "02", "DIMEX": "03", "NITE": "04", "EXTRANJERO": "05"}

        result = await self.send_comprobante(
            clave             = clave,
            fecha_emision     = fecha_emision,
            emisor_tipo       = tipo_map.get(emisor.get("tipo_cedula", "JURIDICA"), "02"),
            emisor_cedula     = emisor["cedula"],
            receptor_tipo     = tipo_map.get(receptor.get("tipo_cedula", "FISICA"), "01") if receptor else None,
            receptor_cedula   = receptor["cedula"] if receptor else None,
            tipo_comprobante  = tipo_comprobante,
            xml_b64           = xml_b64,
        )

        if not poll_status:
            return result

        # Polling para obtener respuesta
        elapsed = 0
        while elapsed < poll_max_seconds:
            await asyncio.sleep(5)
            elapsed += 5
            status = await self.get_comprobante_status(clave)
            hacienda_status = status.get("hacienda_status", "procesando")
            if hacienda_status not in ("procesando", "no_encontrado"):
                return {**result, "final_status": status}

        return {**result, "final_status": {"hacienda_status": "procesando", "timeout": True}}
