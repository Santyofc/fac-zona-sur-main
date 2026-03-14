"""
Pydantic Schemas (Request/Response) — Factura CR
"""
from pydantic import BaseModel, EmailStr, UUID4, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────
class CedulaType(str, Enum):
    FISICA = "FISICA"
    JURIDICA = "JURIDICA"
    DIMEX = "DIMEX"
    NITE = "NITE"
    EXTRANJERO = "EXTRANJERO"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    PROCESSING = "processing"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DocType(str, Enum):
    FE = "FE"   # Factura Electrónica
    TE = "TE"   # Tiquete Electrónico
    NC = "NC"   # Nota de Crédito
    ND = "ND"   # Nota de Débito


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    ACCOUNTANT = "accountant"
    VIEWER = "viewer"


class PaymentMethod(str, Enum):
    PAYPAL = "paypal"
    MANUAL = "manual"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"




# ─── Auth ─────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=2)
    company_name: str = Field(..., min_length=2)
    company_cedula: str
    company_cedula_type: CedulaType = CedulaType.JURIDICA
    company_phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    company_id: str


# ─── Client ───────────────────────────────────────────────────
class ClientBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    cedula_type: CedulaType = CedulaType.FISICA
    cedula_number: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    province: Optional[str] = None
    canton: Optional[str] = None
    district: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class ClientUpdate(ClientBase):
    name: Optional[str] = None
    cedula_type: Optional[CedulaType] = None
    is_active: Optional[bool] = None


class ClientResponse(ClientBase):
    id: UUID4
    company_id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Product ──────────────────────────────────────────────────
class ProductBase(BaseModel):
    code: Optional[str] = None
    cabys_code: Optional[str] = None
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    unit_price: Decimal = Field(..., ge=0, decimal_places=5)
    currency: str = Field(default="CRC", max_length=3)
    tax_rate: Decimal = Field(default=Decimal("13.0"), decimal_places=2)
    unit_measure: str = Field(default="Sp", max_length=20)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    name: Optional[str] = None
    unit_price: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: UUID4
    company_id: UUID4
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Invoice Items ────────────────────────────────────────────
class InvoiceItemCreate(BaseModel):
    product_id: Optional[UUID4] = None
    cabys_code: Optional[str] = None
    description: str = Field(..., max_length=500)
    unit_measure: str = Field(default="Sp", max_length=20)
    quantity: Decimal = Field(default=Decimal("1"), gt=0, decimal_places=5)
    unit_price: Decimal = Field(..., ge=0, decimal_places=5)
    discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100, decimal_places=2)
    tax_rate: Decimal = Field(default=Decimal("13.0"), decimal_places=2)


class InvoiceItemResponse(InvoiceItemCreate):
    id: UUID4
    invoice_id: UUID4
    line_number: int
    discount_amount: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    total: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Invoice ──────────────────────────────────────────────────
class InvoiceCreate(BaseModel):
    client_id: Optional[UUID4] = None
    doc_type: DocType = DocType.FE
    issue_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    currency: str = Field(default="CRC", max_length=3)
    exchange_rate: Decimal = Field(default=Decimal("1.0"), gt=0, decimal_places=5)
    sale_condition: str = Field(default="01", max_length=5)
    payment_method: str = Field(default="01", max_length=5)
    credit_term_days: int = Field(default=0, ge=0)
    notes: Optional[str] = None
    items: List[InvoiceItemCreate] = Field(..., min_length=1)


class InvoiceResponse(BaseModel):
    id: UUID4
    company_id: UUID4
    client_id: Optional[UUID4]
    client: Optional[ClientResponse]
    consecutive: str
    clave: Optional[str]
    doc_type: str
    issue_date: datetime
    due_date: Optional[datetime]
    currency: str
    exchange_rate: Decimal
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    total: Decimal
    sale_condition: str
    payment_method: str
    credit_term_days: int
    status: str
    notes: Optional[str]
    items: List[InvoiceItemResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvoiceListItem(BaseModel):
    id: UUID4
    consecutive: str
    clave: Optional[str]
    doc_type: str
    issue_date: datetime
    total: Decimal
    currency: str
    status: str
    client_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Hacienda ─────────────────────────────────────────────────
class HaciendaStatusResponse(BaseModel):
    invoice_id: UUID4
    status: str
    hacienda_status: Optional[str]
    hacienda_msg: Optional[str]
    submission_date: Optional[datetime]
    response_date: Optional[datetime]
    send_attempts: int
    pdf_url: Optional[str]

    class Config:
        from_attributes = True


# ─── Dashboard Stats ──────────────────────────────────────────
class DashboardStats(BaseModel):
    revenue_month: Decimal
    invoices_issued: int
    tax_accumulated: Decimal
    invoices_pending: int
    invoices_accepted: int
    invoices_rejected: int


# ─── Generic ──────────────────────────────────────────────────
class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None


class PaginatedResponse(BaseModel):
    total: int
    page: int
    per_page: int
    pages: int


# ─── Payments ─────────────────────────────────────────────────
class PaymentBase(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)
    payment_method: PaymentMethod
    reference_id: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    pass


class PaymentUpdate(BaseModel):
    status: Optional[PaymentStatus] = None
    notes: Optional[str] = None


class PaymentResponse(PaymentBase):
    id: UUID4
    company_id: UUID4
    status: PaymentStatus
    months_added: int
    approved_at: Optional[datetime] = None
    approved_by: Optional[UUID4] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PayPalOrderRequest(BaseModel):
    plan_id: str  # identifier for the plan being purchased
    months: int = Field(default=1, gt=0)

