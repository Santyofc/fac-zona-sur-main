"""
SQLAlchemy ORM Models — Factura CR
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Boolean, Numeric, Integer, SmallInteger,
    Text, ForeignKey, DateTime, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Company(Base):
    __tablename__ = "companies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    name = Column(String(255), nullable=False)
    trade_name = Column(String(255))
    cedula_type = Column(String(10), nullable=False, default="JURIDICA")
    cedula_number = Column(String(20), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(30))
    website = Column(String(255))
    province = Column(String(100))
    canton = Column(String(100))
    district = Column(String(100))
    address = Column(Text)
    hacienda_user = Column(String(255))
    hacienda_pass_encrypted = Column(Text)
    cert_path = Column(String(500))
    cert_pin_encrypted = Column(Text)
    invoice_prefix = Column(String(10), default="E-")
    consecutive_num = Column(BigInteger, nullable=False, default=1)
    economic_activity = Column(String(10))
    plan = Column(String(20), nullable=False, default="free")
    plan_expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    users = relationship("User", back_populates="company", cascade="all, delete-orphan")
    clients = relationship("Client", back_populates="company", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="company", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="company", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="company", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(Text)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500))
    role = Column(String(20), nullable=False, default="viewer")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True))

    company = relationship("Company", back_populates="users")


class Client(Base):
    __tablename__ = "clients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    cedula_type = Column(String(10), nullable=False, default="FISICA")
    cedula_number = Column(String(20))
    email = Column(String(255))
    phone = Column(String(30))
    province = Column(String(100))
    canton = Column(String(100))
    district = Column(String(100))
    address = Column(Text)
    notes = Column(Text)
    is_active = Column(Boolean, nullable=False, default=True)

    company = relationship("Company", back_populates="clients")
    invoices = relationship("Invoice", back_populates="client")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(50))
    cabys_code = Column(String(20))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    unit_price = Column(Numeric(12, 5), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="CRC")
    tax_rate = Column(Numeric(5, 2), nullable=False, default=13.0)
    unit_measure = Column(String(20), nullable=False, default="Sp")
    is_active = Column(Boolean, nullable=False, default=True)

    company = relationship("Company", back_populates="products")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"))
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    consecutive = Column(String(20), nullable=False)
    clave = Column(String(50), unique=True)
    doc_type = Column(String(5), nullable=False, default="FE")
    issue_date = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime(timezone=True))
    currency = Column(String(3), nullable=False, default="CRC")
    exchange_rate = Column(Numeric(12, 5), default=1.0)
    subtotal = Column(Numeric(12, 5), nullable=False, default=0)
    tax_total = Column(Numeric(12, 5), nullable=False, default=0)
    discount_total = Column(Numeric(12, 5), nullable=False, default=0)
    total = Column(Numeric(12, 5), nullable=False, default=0)
    sale_condition = Column(String(5), nullable=False, default="01")
    payment_method = Column(String(5), nullable=False, default="01")
    credit_term_days = Column(Integer, default=0)
    status = Column(String(20), nullable=False, default="draft")
    notes = Column(Text)

    company = relationship("Company", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    hacienda_doc = relationship("HaciendaDocument", back_populates="invoice", uselist=False)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))

    line_number = Column(SmallInteger, nullable=False)
    cabys_code = Column(String(20))
    description = Column(String(500), nullable=False)
    unit_measure = Column(String(20), nullable=False, default="Sp")
    quantity = Column(Numeric(12, 5), nullable=False, default=1)
    unit_price = Column(Numeric(12, 5), nullable=False)
    discount_pct = Column(Numeric(5, 2), default=0)
    discount_amount = Column(Numeric(12, 5), default=0)
    subtotal = Column(Numeric(12, 5), nullable=False)
    tax_rate = Column(Numeric(5, 2), nullable=False, default=13.0)
    tax_amount = Column(Numeric(12, 5), nullable=False)
    total = Column(Numeric(12, 5), nullable=False)

    invoice = relationship("Invoice", back_populates="items")


class HaciendaDocument(Base):
    __tablename__ = "hacienda_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, unique=True)
    xml_content = Column(Text)
    xml_signed = Column(Text)
    xml_filename = Column(String(255))
    submission_date = Column(DateTime(timezone=True))
    hacienda_status = Column(String(20))
    hacienda_msg = Column(Text)
    hacienda_detail = Column(Text)
    response_xml = Column(Text)
    response_date = Column(DateTime(timezone=True))
    pdf_url = Column(String(500))
    pdf_generated_at = Column(DateTime(timezone=True))
    send_attempts = Column(SmallInteger, nullable=False, default=0)
    invoice = relationship("Invoice", back_populates="hacienda_doc")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    payment_method = Column(String(20), nullable=False)  # 'paypal' or 'manual'
    
    reference_id = Column(String(255))
    receipt_url = Column(String(500))
    
    status = Column(String(20), nullable=False, default="pending")
    months_added = Column(Integer, nullable=False, default=1)
    
    approved_at = Column(DateTime(timezone=True))
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    notes = Column(Text)

    company = relationship("Company", back_populates="payments")
    approver = relationship("User", foreign_keys=[approved_by])

