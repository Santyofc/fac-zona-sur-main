"""
Auth Router — Register, Login and Hub Token Exchange.
"""
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import jwt, JWTError, ExpiredSignatureError

from database import get_db
from models.models import Company, User
from schemas.schemas import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    ModuleExchangeRequest,
    ModuleExchangeResponse,
)
from config import settings
from services.module_exchange_service import mark_jti_once
from routers.deps import get_current_user
from limiter import limiter

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _error(status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
            }
        },
    )


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


def _map_hub_role_to_local(hub_role: str) -> str:
    mapping = {
        "owner": "owner",
        "admin": "admin",
        "operator": "accountant",
        "viewer": "viewer",
    }
    return mapping.get(hub_role, "viewer")


def _safe_redirect_path(path: str | None) -> str:
    if not path:
        return settings.MODULE_DASHBOARD_PATH
    if not path.startswith("/") or path.startswith("//"):
        return settings.MODULE_DASHBOARD_PATH
    return path


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register(request: Request, data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")

    company = Company(
        name=data.company_name,
        cedula_type=data.company_cedula_type.value,
        cedula_number=data.company_cedula,
        email=data.email,
        phone=data.company_phone,
        plan="free",
    )
    db.add(company)
    await db.flush()

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
@limiter.limit("10/minute")
async def login(request: Request, data: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.password_hash or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas.",
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada.")

    user.last_login_at = datetime.utcnow()

    token = create_access_token(str(user.id), str(user.company_id))
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
        user_id=str(user.id),
        company_id=str(user.company_id),
    )


@router.post("/exchange", response_model=ModuleExchangeResponse)
async def exchange_module_token(
    payload: ModuleExchangeRequest,
    db: AsyncSession = Depends(get_db),
):
    if not settings.HUB_TOKEN_SHARED_SECRET:
        return _error(500, "SERVER_MISCONFIGURED", "HUB_TOKEN_SHARED_SECRET is not configured.")

    try:
        claims = jwt.decode(
            payload.token,
            settings.HUB_TOKEN_SHARED_SECRET,
            algorithms=[settings.HUB_TOKEN_ALGORITHM],
            issuer=settings.HUB_TOKEN_ISSUER,
            audience=settings.HUB_TOKEN_AUDIENCE,
        )
    except ExpiredSignatureError:
        return _error(401, "TOKEN_EXPIRED", "Exchange token expired.")
    except JWTError:
        return _error(401, "INVALID_TOKEN", "Exchange token is invalid.")

    required_claims = ["sub", "tenant_id", "module_key", "jti", "exp", "role"]
    missing = [key for key in required_claims if key not in claims]
    if missing:
        return _error(422, "INVALID_CLAIMS", f"Missing required claims: {', '.join(missing)}")

    module_key = str(claims["module_key"])
    if module_key != settings.HUB_EXPECTED_MODULE_KEY:
        return _error(403, "INVALID_MODULE", "module_key does not match this service.")

    tenant_id = str(claims["tenant_id"])
    jti = str(claims["jti"])
    hub_user_id = str(claims["sub"])
    hub_role = str(claims["role"])
    exp_ts = int(claims["exp"])
    now_ts = int(datetime.now(tz=timezone.utc).timestamp())

    if exp_ts <= now_ts:
        return _error(401, "TOKEN_EXPIRED", "Exchange token expired.")

    ttl = exp_ts - now_ts
    try:
        accepted = await mark_jti_once(jti, ttl_seconds=ttl)
    except Exception:
        return _error(503, "REPLAY_STORE_UNAVAILABLE", "Replay protection store unavailable.")

    if not accepted:
        return _error(409, "TOKEN_REPLAYED", "Exchange token already used.")

    company_result = await db.execute(
        select(Company).where(Company.id == uuid.UUID(tenant_id), Company.is_active.is_(True))
    )
    company = company_result.scalar_one_or_none()
    if not company:
        return _error(404, "TENANT_NOT_FOUND", "tenant_id is not valid in billing module.")

    synthetic_email = f"{hub_user_id}@hub.zonasurtech.local"
    user_result = await db.execute(
        select(User).where(User.company_id == company.id, User.email == synthetic_email)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        user = User(
            company_id=company.id,
            email=synthetic_email,
            password_hash=None,
            full_name=f"Hub User {hub_user_id[:8]}",
            role=_map_hub_role_to_local(hub_role),
            is_active=True,
            last_login_at=datetime.utcnow(),
        )
        db.add(user)
        await db.flush()
    else:
        user.role = _map_hub_role_to_local(hub_role)
        user.last_login_at = datetime.utcnow()

    local_access_token = create_access_token(str(user.id), str(company.id))
    expires_in = settings.JWT_EXPIRE_MINUTES * 60
    expires_at = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
    redirect_to = _safe_redirect_path(payload.redirect_path)

    response_payload = ModuleExchangeResponse(
        access_token=local_access_token,
        expires_in=expires_in,
        expires_at=expires_at,
        user_id=str(user.id),
        company_id=str(company.id),
        tenant_id=tenant_id,
        module_key=module_key,
        jti=jti,
        redirect_to=redirect_to,
    )

    if payload.redirect:
        redirect_response = RedirectResponse(url=redirect_to, status_code=303)
        redirect_response.set_cookie(
            key=settings.MODULE_SESSION_COOKIE_NAME,
            value=local_access_token,
            max_age=expires_in,
            httponly=True,
            secure=settings.MODULE_SESSION_COOKIE_SECURE,
            samesite=settings.MODULE_SESSION_COOKIE_SAMESITE,
            path="/",
        )
        return redirect_response

    json_response = JSONResponse(content=response_payload.model_dump(mode="json"), status_code=200)
    json_response.set_cookie(
        key=settings.MODULE_SESSION_COOKIE_NAME,
        value=local_access_token,
        max_age=expires_in,
        httponly=True,
        secure=settings.MODULE_SESSION_COOKIE_SECURE,
        samesite=settings.MODULE_SESSION_COOKIE_SAMESITE,
        path="/",
    )
    return json_response


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    "`"`"Retorna el perfil del usuario actual y su empresa."`"`"
    company_result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = company_result.scalar_one_or_none()
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "company": {
            "id": str(company.id),
            "name": company.name,
            "plan": company.plan,
        } if company else None
    }
