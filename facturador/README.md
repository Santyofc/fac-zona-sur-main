# Facturador Fiscal CR

Servicio standalone de facturacion electronica CR v4.4 con arquitectura portable:
- `domain/` y `application/` desacoplados de FastAPI/Celery/ORM
- adaptadores en `infrastructure/`
- transporte en `interfaces/http`
- workers en `workers/`

## Requisitos
- Python 3.12+
- Docker (opcional)

## Ejecutar con Docker
```bash
docker compose up --build
```
API: `http://localhost:8080`

## Ejecutar local
```bash
pip install -e .[test]
uvicorn app.main:app --reload --port 8080
```

## Migraciones
```bash
alembic upgrade head
```

## Workers
```bash
celery -A app.workers.celery_app.celery_app worker -Q issue_document,check_document_status,send_document_email --loglevel=info
```

## Endpoints principales
- `POST /v1/invoices`
- `POST /v1/invoices/{id}/issue`
- `GET /v1/invoices/{id}/status`
- `POST /v1/invoices/{id}/email`
- `POST /v1/tickets`, `/v1/credit-notes`, `/v1/debit-notes`
- `POST/GET /v1/customers`
- `POST/GET /v1/products`
- `POST /v1/certificates`
- `GET /v1/health`, `GET /v1/readiness`

## Portabilidad
Para integrar en POS futuro:
- copiar `app/domain` + `app/application`
- implementar puertos en `application/ports`
- opcionalmente usar `SaleToFiscalDocumentMapper`

## Nota de firma XAdES
La firma está encapsulada en `app/infrastructure/integrations/xml/signer_xades.py` con `signxml` + `cryptography`.
Requiere certificado `.p12` real y credenciales válidas.
