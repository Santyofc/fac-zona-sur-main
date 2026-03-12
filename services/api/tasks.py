"""
tasks.py — Celery Workers para Factura CR
Background jobs: envío a Hacienda, consulta de estado, envío de email.

Para ejecutar:
  celery -A tasks worker --loglevel=info --concurrency=4
  celery -A tasks beat --loglevel=info   # Para tareas programadas
"""

from __future__ import annotations

import logging
import os

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

# ─── Config Celery ────────────────────────────────────────────────────────────
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "factura_cr",
    broker   = REDIS_URL,
    backend  = REDIS_URL,
)

celery_app.conf.update(
    task_serializer        = "json",
    accept_content         = ["json"],
    result_serializer      = "json",
    timezone               = "America/Costa_Rica",
    enable_utc             = True,
    task_track_started     = True,
    task_acks_late         = True,
    worker_prefetch_multiplier = 1,   # Fair distribution
    task_max_retries       = 3,
    task_default_retry_delay = 30,    # 30 segundos entre reintentos
)


# ─── Beat Schedule (tareas programadas) ───────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Consulta estado de comprobantes pendientes cada 5 minutos
    "check-pending-invoices": {
        "task":     "tasks.check_pending_invoices",
        "schedule": crontab(minute="*/5"),
    },
    # Actualizar tipo de cambio a las 10am hora CR (publicado por BCCR)
    "update-exchange-rate": {
        "task":     "tasks.update_exchange_rate",
        "schedule": crontab(hour=10, minute=0),
    },
}


# ─── TASK: Enviar factura a Hacienda ─────────────────────────────────────────
@celery_app.task(
    bind=True,
    name="tasks.send_invoice_to_hacienda",
    max_retries=3,
    default_retry_delay=60,
)
def send_invoice_to_hacienda(self, invoice_id: str) -> dict:
    """
    Worker: ejecuta el pipeline completo de envío de una factura a Hacienda.

    Flujo:
      1. Cargar factura de la DB
      2. Generar XML v4.4
      3. Firmar con .p12 BCCR
      4. Convertir a Base64
      5. Enviar a API Hacienda
      6. Actualizar estado en DB

    Args:
        invoice_id: UUID de la factura en la DB

    Returns:
        Dict con {status, clave, hacienda_status}
    """
    import asyncio
    from config import get_settings

    logger.info(f"[Worker] 🚀 Iniciando envío de factura {invoice_id}")

    try:
        config = get_settings()
        result = asyncio.run(_async_process_invoice(invoice_id, config))
        logger.info(f"[Worker] ✅ Factura procesada: {invoice_id} → {result.get('status')}")
        return result

    except Exception as exc:
        logger.error(f"[Worker] ❌ Error en factura {invoice_id}: {exc}")
        # Reintentar con backoff exponencial
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


async def _async_process_invoice(invoice_id: str, config) -> dict:
    """Ejecuta el pipeline asíncrono de Hacienda dentro del worker Celery."""
    from database import get_db_session
    from services.hacienda_service import process_invoice_to_hacienda

    async with get_db_session() as db:
        return await process_invoice_to_hacienda(invoice_id, db, config)


# ─── TASK: Verificar estado de comprobantes pendientes ────────────────────────
@celery_app.task(name="tasks.check_pending_invoices")
def check_pending_invoices() -> dict:
    """
    Consulta el estado de todas las facturas en estado 'processing' en Hacienda.
    Se ejecuta cada 5 minutos según el beat schedule.
    """
    import asyncio

    logger.info("[Worker] 🔍 Consultando comprobantes pendientes...")
    try:
        result = asyncio.run(_async_check_pending())
        logger.info(f"[Worker] Comprobantes actualizados: {result}")
        return result
    except Exception as exc:
        logger.error(f"[Worker] ❌ Error en check_pending: {exc}")
        return {"error": str(exc)}


async def _async_check_pending() -> dict:
    """Consulta y actualiza estado de facturas pendientes en la DB."""
    from sqlalchemy import select, update
    from database import get_db_session
    from models.models import Invoice, HaciendaDocument
    from config import get_settings
    from services.hacienda.check_status import check_status, ComprobanteStatus
    from services.hacienda.auth_service import AuthService

    config   = get_settings()
    updated  = 0
    errors   = 0

    auth = AuthService(
        username    = config.HACIENDA_USERNAME,
        password    = config.HACIENDA_PASSWORD,
        environment = config.HACIENDA_ENV,
    )

    async with get_db_session() as db:
        # Buscar facturas con estado 'processing' que tienen clave asignada
        result = await db.execute(
            select(Invoice).where(
                Invoice.status == "processing",
                Invoice.clave != None,
            ).limit(50)
        )
        invoices = result.scalars().all()

        for invoice in invoices:
            try:
                status_result = await check_status(
                    clave       = invoice.clave,
                    auth        = auth,
                    environment = config.HACIENDA_ENV,
                )

                if status_result.status in (
                    ComprobanteStatus.ACEPTADO,
                    ComprobanteStatus.RECHAZADO,
                ):
                    invoice.status = (
                        "accepted" if status_result.status == ComprobanteStatus.ACEPTADO
                        else "rejected"
                    )

                    # Actualizar HaciendaDocument
                    hac_result = await db.execute(
                        select(HaciendaDocument).where(
                            HaciendaDocument.invoice_id == invoice.id
                        )
                    )
                    hac_doc = hac_result.scalar_one_or_none()
                    if hac_doc:
                        hac_doc.hacienda_status  = status_result.status.value
                        hac_doc.hacienda_msg     = status_result.message
                        hac_doc.response_xml     = status_result.respuesta_xml

                    updated += 1

            except Exception as exc:
                logger.error(f"[check_pending] Error al verificar {invoice.clave}: {exc}")
                errors += 1

        await db.commit()

    return {"updated": updated, "errors": errors, "total": len(invoices)}


# ─── TASK: Actualizar tipo de cambio ─────────────────────────────────────────
@celery_app.task(name="tasks.update_exchange_rate")
def update_exchange_rate() -> dict:
    """
    Obtiene el tipo de cambio del BCCR y lo cachea en Redis.
    Se ejecuta diariamente a las 10:00 AM hora Costa Rica.
    """
    import asyncio

    logger.info("[Worker] 💱 Actualizando tipo de cambio BCCR...")
    try:
        result = asyncio.run(_fetch_exchange_rate())
        logger.info(f"[Worker] Tipo de cambio: {result}")
        return result
    except Exception as exc:
        logger.error(f"[Worker] ❌ Error al obtener tipo de cambio: {exc}")
        return {"error": str(exc)}


async def _fetch_exchange_rate() -> dict:
    """Consulta el tipo de cambio en el API público de Hacienda."""
    import httpx

    url = "https://api.hacienda.go.cr/indicadores/tc"
    async with httpx.AsyncClient(timeout=15) as http:
        resp = await http.get(url)
        data = resp.json()

    # El API retorna: {"venta": {"valor": 520.5}, "compra": {"valor": 518.0}}
    venta  = data.get("venta", {}).get("valor", 0)
    compra = data.get("compra", {}).get("valor", 0)

    return {"venta": venta, "compra": compra, "source": "Hacienda CR"}
