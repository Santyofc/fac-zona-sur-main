from fastapi import FastAPI

from app.core.logging import configure_logging
from app.interfaces.http.routes.certificates import router as certificates_router
from app.interfaces.http.routes.credit_notes import router as credit_notes_router
from app.interfaces.http.routes.customers import router as customers_router
from app.interfaces.http.routes.debit_notes import router as debit_notes_router
from app.interfaces.http.routes.health import router as health_router
from app.interfaces.http.routes.invoices import router as invoices_router
from app.interfaces.http.routes.products import router as products_router
from app.interfaces.http.routes.tickets import router as tickets_router

configure_logging()

app = FastAPI(title='Facturador Fiscal CR', version='1.0.0')

app.include_router(invoices_router)
app.include_router(tickets_router)
app.include_router(credit_notes_router)
app.include_router(debit_notes_router)
app.include_router(customers_router)
app.include_router(products_router)
app.include_router(certificates_router)
app.include_router(health_router)
