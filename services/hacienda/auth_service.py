"""
auth_service.py — OAuth2 Token Management para Hacienda CR
Responsabilidad única: obtener y cachear tokens de acceso.

Hacienda usa OAuth2 ROPC (Resource Owner Password Credentials):
  POST /token con grant_type=password + client_id + username + password

Sandbox IDP:
  https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token

Producción IDP:
  https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ─── Endpoints por ambiente ───────────────────────────────────────────────────
TOKEN_ENDPOINTS = {
    "sandbox":    "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token",
    "production": "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token",
}

CLIENT_IDS = {
    "sandbox":    "api-stag",
    "production": "api-prod",
}

# Segundos de margen antes de considerar expirado
TOKEN_EXPIRY_BUFFER = 60
_token_locks: dict[str, asyncio.Lock] = {}


@dataclass
class TokenInfo:
    """Información del token de acceso en caché."""
    access_token:  str
    expires_at:    float       # Unix timestamp
    token_type:    str = "bearer"
    refresh_token: Optional[str] = None


class AuthService:
    """
    Servicio de autenticación OAuth2 para la API de Hacienda CR.

    Maneja:
      - Obtención inicial de token (ROPC grant)
      - Caché en memoria para reutilizar tokens válidos
      - Renovación automática al detectar expiración

    Uso:
      auth = AuthService(username, password, environment="sandbox")
      token = await auth.get_access_token()
    """

    def __init__(
        self,
        username:    str,
        password:    str,
        environment: str = "sandbox",
        timeout:     int  = 20,
    ):
        if environment not in TOKEN_ENDPOINTS:
            raise ValueError(f"Ambiente inválido: '{environment}'. Usar 'sandbox' o 'production'.")

        self.username    = username
        self.password    = password
        self.environment = environment
        self.timeout     = timeout
        self._token_url  = TOKEN_ENDPOINTS[environment]
        self._client_id  = CLIENT_IDS[environment]
        self._cached:    Optional[TokenInfo] = None

    @property
    def is_token_valid(self) -> bool:
        """Verifica si hay token en caché y sigue siendo válido."""
        if not self._cached:
            return False
        return self._cached.expires_at > time.time() + TOKEN_EXPIRY_BUFFER

    @property
    def _lock(self) -> asyncio.Lock:
        return _token_locks.setdefault(f"{self.environment}:{self.username}", asyncio.Lock())

    async def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Retorna el token de acceso vigente.
        Si no hay token o está por expirar, obtiene uno nuevo.

        Args:
            force_refresh: Forzar nuevo token aunque el cacheado sea válido.

        Returns:
            String del access_token JWT de Hacienda.

        Raises:
            AuthenticationError: Si las credenciales son inválidas.
            ConnectionError: Si no se puede conectar al IDP.
        """
        async with self._lock:
            if not force_refresh and self.is_token_valid:
                logger.debug(
                    "[AuthService] ♻️  Token en caché válido — expira en %ss",
                    int(self._cached.expires_at - time.time()),
                )
                return self._cached.access_token

            return await self._fetch_new_token()

    async def _fetch_new_token(self) -> str:
        """Realiza la petición POST /token al IDP de Hacienda."""
        logger.info("[AuthService] 🔑 Solicitando nuevo token | env=%s", self.environment)

        payload = {
            "grant_type": "password",
            "client_id":  self._client_id,
            "username":   self.username,
            "password":   self.password,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as http:
            try:
                resp = await http.post(
                    self._token_url,
                    data=payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
            except httpx.ConnectError as exc:
                raise ConnectionError(
                    f"No se pudo conectar al IDP de Hacienda CR: {exc}\n"
                    f"URL: {self._token_url}"
                ) from exc
            except httpx.TimeoutException as exc:
                raise ConnectionError(f"Timeout al conectar al IDP: {exc}") from exc

        if resp.status_code == 401:
            raise AuthenticationError(
                "Credenciales inválidas para el ATV de Hacienda.\n"
                f"Respuesta: {resp.text[:300]}"
            )

        if resp.status_code != 200:
            raise AuthenticationError(
                f"Error inesperado del IDP Hacienda (HTTP {resp.status_code}):\n{resp.text[:300]}"
            )

        data         = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise AuthenticationError(f"IDP no retornó access_token. Respuesta: {data}")

        expires_in     = int(data.get("expires_in", 300))
        refresh_token  = data.get("refresh_token")

        self._cached = TokenInfo(
            access_token  = access_token,
            expires_at    = time.time() + expires_in,
            refresh_token = refresh_token,
        )

        logger.info(f"[AuthService] ✅ Token obtenido — expira en {expires_in}s")
        return access_token

    def invalidate(self) -> None:
        """Invalida el token en caché. El próximo acceso forzará una nueva autenticación."""
        self._cached = None
        logger.info("[AuthService] Token invalidado manualmente.")

    async def get_auth_header(self, force_refresh: bool = False) -> dict[str, str]:
        """
        Retorna el header Authorization listo para usar en peticiones HTTP.

        Returns:
            {"Authorization": "Bearer <access_token>"}
        """
        token = await self.get_access_token(force_refresh=force_refresh)
        return {"Authorization": f"Bearer {token}"}


class AuthenticationError(Exception):
    """Error de autenticación con el sistema Hacienda CR."""
    pass
