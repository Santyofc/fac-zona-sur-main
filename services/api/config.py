"""
Configuración global de la aplicación usando Pydantic Settings.
Lee variables desde el archivo .env en la raíz del servicio.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # ─── App ──────────────────────────────────────────────
    APP_NAME: str = "Factura CR"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "changeme-in-production"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://app.facturacr.com",
    ]

    # ─── Database ─────────────────────────────────────────
    ASYNC_DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/factura_cr"
    DATABASE_URL: str = "" # Fallback

    # ─── Redis / Celery ───────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # ─── JWT ──────────────────────────────────────────────
    JWT_SECRET: str = "changeme-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24h

    # ─── Supabase ─────────────────────────────────────────
    SUPABASE_URL: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # ─── Hacienda Costa Rica ──────────────────────────────
    HACIENDA_API_URL: str = "https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1"
    HACIENDA_TOKEN_URL: str = "https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token"
    HACIENDA_CLIENT_ID: str = ""
    HACIENDA_CLIENT_SECRET: str = ""
    HACIENDA_USERNAME: str = ""
    HACIENDA_PASSWORD: str = ""

    # ─── Firma Digital ────────────────────────────────────
    FIRMA_DIGITAL_PATH: str = "./certs/firma.p12"
    FIRMA_DIGITAL_PIN: str = ""

    # ─── Storage ──────────────────────────────────────────
    STORAGE_BUCKET: str = "facturas-pdf"

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()
