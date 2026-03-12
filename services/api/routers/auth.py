"""
Auth Router — Register & Login con JWT
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import uuid

from database import get_db
from models.models import Company, User
from schemas.schemas import RegisterRequest, LoginRequest, TokenResponse, MessageResponse
from config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: str, company_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "company_id": company_id,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Registrar una nueva empresa + usuario owner."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")

    # Create Company
    company = Company(
        name=data.company_name,
        cedula_type=data.company_cedula_type.value,
        cedula_number=data.company_cedula,
        email=data.email,
        phone=data.company_phone,
        plan="free",
    )
    db.add(company)
    await db.flush()  # get company.id

    # Create Owner User
    user = User(
        company_id=company.id,
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role="owner",
    )
    db.add(user)
    await db.flush()

    token = create_access_token(str(user.id), str(company.id))
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        company_id=str(company.id),
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Iniciar sesión con email y contraseña."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada.")

    # Update last login
    user.last_login_at = datetime.utcnow()

    token = create_access_token(str(user.id), str(user.company_id))
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        company_id=str(user.company_id),
    )
