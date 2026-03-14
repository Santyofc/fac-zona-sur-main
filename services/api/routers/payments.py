"""
API Routers for Subscription Payments (PayPal & Manual/SINPE)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime, timedelta
import httpx

from database import get_db
from models.models import User, Company, Payment
from schemas.schemas import (
    PaymentResponse, PaymentCreate, PaymentUpdate, PaymentMethod, PaymentStatus,
    PayPalOrderRequest, MessageResponse
)
from routers.deps import get_current_user
from config import settings

router = APIRouter()

# ─── Mocks for PayPal (Replace with actual PayPal SDK/HTTP calls) ────
# Using HTTPX to call PayPal REST API
async def get_paypal_access_token() -> str:
    """Obtains an access token from PayPal API."""
    # In a real app, you would cache this token until it expires
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
    data = {"grant_type": "client_credentials"}
    
    # Use sandbox or api-m depending on environment
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, auth=auth, data=data)
        if response.status_code != 200:
            raise Exception("Failed to get PayPal access token")
        return response.json()["access_token"]


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
    # 1. Definir montos fijos por ahora (Ideal: buscar por plan_id en DB)
    amount_per_month = 19.99  # Ejemplo para el plan Pro
    total_amount = amount_per_month * request.months
    
    # 2. Llamada a la API de PayPal para crear la orden
    try:
        # access_token = await get_paypal_access_token()
        # paypal_url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
        # headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        # payload = { ... } # Intent: CAPTURE, purchase_units
        
        # MOCK para el ejemplo:
        order_id = f"PAYPAL-MOCK-ORDER-{datetime.now().timestamp()}"
        
        # Guardar intención de pago en DB (opcional o se crea en capture)
        new_payment = Payment(
            company_id=current_user.company_id,
            amount=total_amount,
            currency="USD",
            payment_method=PaymentMethod.PAYPAL,
            reference_id=order_id,
            status=PaymentStatus.PENDING,
            months_added=request.months
        )
        db.add(new_payment)
        await db.commit()
        
        return {"order_id": order_id, "amount": total_amount, "currency": "USD"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    # 1. Buscar el pago local
    result = await db.execute(select(Payment).where(Payment.reference_id == order_id))
    payment = result.scalar_one_or_none()
    
    if not payment:
         raise HTTPException(status_code=404, detail="Order not found")
         
    if payment.status == PaymentStatus.APPROVED:
        return {"message": "Payment already captured"}
        
    # 2. Llamar a PayPal para capturar el pago
    # access_token = await get_paypal_access_token()
    # MOCK: asumimos exito
    capture_status = "COMPLETED" 
    
    if capture_status == "COMPLETED":
        # 3. Actualizar estado del pago
        payment.status = PaymentStatus.APPROVED
        payment.approved_at = datetime.utcnow()
        
        # 4. Actualizar plan_expires_at de la empresa
        result = await db.execute(select(Company).where(Company.id == current_user.company_id))
        company = result.scalar_one()
        
        now = datetime.utcnow()
        current_exp = company.plan_expires_at.replace(tzinfo=None) if company.plan_expires_at else now
        if current_exp < now:
            current_exp = now
            
        # Añadir meses aprox
        new_exp = current_exp + timedelta(days=30 * payment.months_added)
        company.plan_expires_at = new_exp
        
        await db.commit()
        return {"message": "Payment successful. Subscription extended.", "detail": str(new_exp.date())}
    else:
        payment.status = PaymentStatus.REJECTED
        await db.commit()
        raise HTTPException(status_code=400, detail="Payment capture failed in PayPal")


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
