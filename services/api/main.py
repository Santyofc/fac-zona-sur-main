"""
Factura CR — FastAPI Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager

from config import settings
from database import engine, Base
from limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from routers import auth, clients, products, invoices, hacienda, payments

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle handler."""
    # Startup: create tables if they don't exist (dev mode)
    if settings.APP_ENV == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown cleanup (si fuera necesario)
    await engine.dispose()


app = FastAPI(
    title="Factura CR API",
    description="API de facturación electrónica para Costa Rica — Zona Sur Tech",
    version="1.0.0",
    contact={
        "name": "Zona Sur Tech",
        "url": "https://zonasurtech.online",
        "email": "dev@zonasurtech.online",
    },
    license_info={
        "name": "Proprietary",
    },
    lifespan=lifespan,
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
)

# ─── Rate Limiting ───────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────
app.include_router(auth.router,     prefix="/auth",     tags=["Auth"])
app.include_router(clients.router,  prefix="/clients",  tags=["Clients"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
app.include_router(hacienda.router, prefix="/invoices", tags=["Hacienda"])
app.include_router(payments.router, prefix="/payments", tags=["Payments"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Factura CR API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.APP_ENV,
    }


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}
