from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    APP_ENV: str = 'development'
    APP_NAME: str = 'facturador'
    APP_PORT: int = 8080
    APP_DEBUG: bool = True

    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    HACIENDA_ENV: str = 'sandbox'
    HACIENDA_API_URL: str
    HACIENDA_TOKEN_URL: str
    HACIENDA_CLIENT_ID: str = 'api-stag'
    HACIENDA_CLIENT_SECRET: str = ''
    HACIENDA_USERNAME: str = ''
    HACIENDA_PASSWORD: str = ''

    STORAGE_ROOT: str = './.storage'
    CERT_STORAGE_ROOT: str = './.certs'

    EMAIL_FROM: str = 'noreply@facturador.local'
    SMTP_HOST: str = 'localhost'
    SMTP_PORT: int = 1025
    SMTP_USERNAME: str = ''
    SMTP_PASSWORD: str = ''


settings = Settings()
