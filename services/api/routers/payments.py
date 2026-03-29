"""
API Routers for Subscription Payments (PayPal & Manual/SINPE)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
import httpx
import logging

from database import get_db
from models.models import User, Company, Payment
from schemas.schemas import (
    PaymentResponse, PaymentCreate, PaymentUpdate, PaymentMethod, PaymentStatus,
    PayPalOrderRequest, MessageResponse
)
from routers.deps import get_current_user
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── PayPal Functions ──────────────────────────────────────────────────────
async def get_paypal_access_token() -> str:
    """Obtiene un access token real de PayPal API."""
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
    data = {"grant_type": "client_credentials"}
    
    paypal_mode = settings.PAYPAL_MODE or "sandbox"
    if paypal_mode == "production":
        url = "https://api-m.paypal.com/v1/oauth2/token"
    else:
        url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(url, auth=auth, data=data)
        if response.status_code != 200:
            logger.error(f"PayPal auth error: {response.text}")
            raise HTTPException(status_code=500, detail="Failed to authenticate with PayPal")
        return response.json()["access_token"]


async def is_paypal_configured() -> bool:
    """Verifica si PayPal está correctamente configurado."""
    return bool(settings.PAYPAL_CLIENT_ID and settings.PAYPAL_SECRET)


# ─── API Endpoints ────────────────────────────────────────────────────────
@router.get("/history", response_model=list[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Obtiene el historial de pagos de la empresa actual."""
    result = await db.execute(
        select(Payment)
        .where(Payment.company_id == current_user.company_id)
        .order_by(desc(Payment.created_at))
    )
    return result.scalars().all()


@router.post("/paypal/create", response_model=dict)
async def create_paypal_order(
    request: PayPalOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Crea una orden en PayPal para pagar 'n' meses de suscripción.
    Devuelve el order_id para que el frontend inicie el flujo de checkout.
    """
    # Validar configuración
    if not (await is_paypal_configured()):
        logger.warning("PayPal not configured, using mock order")
        # MOCK: si no está configurado, devolver mock
        order_id = f"MOCK-{datetime.now().timestamp()}"
        return {"order_id": order_id, "amount": 19.99 * request.months, "currency": "USD", "mock": True}
    
    try:
        # Montos por plan
        amount_per_month = 19.99  # Se podría parametrizar por plan
        total_amount = amount_per_month * request.months
        
        # Obtener access token
        access_token = await get_paypal_access_token()
        
        # URL según ambiente
        paypal_mode = settings.PAYPAL_MODE or "sandbox"
        if paypal_mode == "production":
            paypal_url = "https://api-m.paypal.com/v2/checkout/orders"
        else:
            paypal_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Payload para PayPal
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {
                    "currency_code": "USD",
                    "value": str(total_amount)
                },
                "reference_id": str(current_user.company_id),
                "description": f"Suscripción Factura CR - {request.months} mes(es)"
            }],
            "return_url": f"{settings.FRONTEND_URL}/settings/billing?status=success&order_id={{order_id}}",
            "cancel_url": f"{settings.FRONTEND_URL}/settings/billing?status=cancel"
        }
        
        # Crear orden en PayPal
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(paypal_url, headers=headers, json=payload)
            
            if response.status_code != 201:
                logger.error(f"PayPal create order error: {response.text}")
                raise HTTPException(status_code=500, detail="Failed to create PayPal order")
            
            order_data = response.json()
            order_id = order_data["id"]
        
        # Guardar registro local de intento de pago
        new_payment = Payment(
            company_id=current_user.company_id,
            amount=total_amount,
            currency="USD",
            payment_method="paypal",
            reference_id=order_id,
            status="pending",
            months_added=request.months
        )
        db.add(new_payment)
        await db.commit()
        
        logger.info(f"✅ PayPal order created: {order_id}")
        return {
            "order_id": order_id, 
            "amount": total_amount,
            "currency": "USD",
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating PayPal order: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error processing payment")


@router.post("/paypal/capture", response_model=MessageResponse)
async def capture_paypal_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Llamado por el frontend DESPUÉS de que el usuario aprueba el pago en PayPal.
    Captura los fondos y actualiza la suscripción.
    """
    # Buscar el pago local
    result = await db.execute(select(Payment).where(Payment.reference_id == order_id))
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if payment.status == "approved":
        return {"message": "Payment already captured"}
    
    try:
        # Si PayPal no está configurado, usar mock
        if not (await is_paypal_configured()):
            logger.warning("PayPal not configured, using mock capture")
            capture_status = "COMPLETED"
        else:
            # Obtener access token
            access_token = await get_paypal_access_token()
            
            # URL según ambiente
            paypal_mode = settings.PAYPAL_MODE or "sandbox"
            if paypal_mode == "production":
                paypal_url = f"https://api-m.paypal.com/v2/checkout/orders/{order_id}/capture"
            else:
                paypal_url = f"https://api-m.sandbox.paypal.com/v2/checkout/orders/{order_id}/capture"
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Capturar pago en PayPal
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(paypal_url, headers=headers, json={})
                
                if response.status_code not in (200, 201):
                    logger.error(f"PayPal capture error: {response.text}")
                    payment.status = "rejected"
                    await db.commit()
                    raise HTTPException(status_code=400, detail="Payment capture failed")
                
                capture_data = response.json()
                capture_status = capture_data.get("status")
        
        if capture_status == "COMPLETED":
            # Actualizar estado del pago
            payment.status = "approved"
            payment.approved_at = datetime.utcnow()
            
            # Actualizar plan_expires_at de la empresa
            company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
            company = company_result.scalar_one()
            
            now = datetime.utcnow()
            current_exp = company.plan_expires_at.replace(tzinfo=None) if company.plan_expires_at else now
            if current_exp < now:
                current_exp = now
            
            # Añadir meses (30 días aprox)
            new_exp = current_exp + timedelta(days=30 * payment.months_added)
            company.plan_expires_at = new_exp
            
            await db.commit()
            logger.info(f"✅ Payment approved: {order_id}, new expiry: {new_exp.date()}")
            return {"message": "Payment successful. Subscription extended.", "detail": str(new_exp.date())}
        else:
            payment.status = "rejected"
            await db.commit()
            logger.warning(f"Payment not completed: {capture_status}")
            raise HTTPException(status_code=400, detail=f"Payment not completed: {capture_status}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error capturing PayPal order: {e}")
        payment.status = "rejected"
        await db.commit()
        raise HTTPException(status_code=500, detail="Unexpected error processing payment")


@router.post("/manual", response_model=PaymentResponse)
async def submit_manual_payment(
    request: PaymentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Sube un reporte de pago manual (SINPE).
    Se queda en estado pending hasta que un admin lo apruebe.
    """
    if request.payment_method != PaymentMethod.MANUAL:
        raise HTTPException(status_code=400, detail="Use manual payment method for this endpoint")
    
    new_payment = Payment(
        company_id=current_user.company_id,
        amount=request.amount,
        currency=request.currency,
        payment_method=PaymentMethod.MANUAL,
        reference_id=request.reference_id,
        receipt_url=request.receipt_url,
        notes=request.notes,
        status=PaymentStatus.PENDING,
        months_added=1  # Default, puede venir en request
    )
    
    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)
    
    return new_payment
