# Factura CR — SaaS de Facturación Electrónica para Costa Rica

[![Hacienda v4.4](https://img.shields.io/badge/Hacienda%20CR-v4.4-blue)](https://www.hacienda.go.cr)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688)](https://fastapi.tiangolo.com)
[![Nuxt 3](https://img.shields.io/badge/Nuxt-3-00DC82)](https://nuxt.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB)](https://python.org)

Plataforma SaaS multiempresa para emisión de comprobantes electrónicos válidos ante el Ministerio de Hacienda de Costa Rica. Implementa el estándar **Comprobantes Electrónicos v4.4** con firma digital XAdES-BES, generación XML, envío a API Hacienda y dashboard financiero.

---

## ✅ Funcionalidades

| Módulo | Estado | Descripción |
|--------|--------|-------------|
| Clave 50 dígitos | ✅ | Generador exacto según spec Hacienda |
| XML v4.4 | ✅ | FE, TE, NC, ND con IVA, CABYS, descuentos |
| Firma XAdES-BES | ✅ | Con certificado .p12 del BCCR |
| OAuth2 Hacienda | ✅ | Token automático con caché |
| Envío a Hacienda | ✅ | POST /recepcion con retry |
| Consulta estado | ✅ | GET /recepcion/{clave} |
| PDF con QR | ✅ | ReportLab + qrcode |
| Dashboard | ✅ | Nuxt 3 + Chart.js |
| Celery Workers | ✅ | Envío y polling en background |
| Multi-empresa | ✅ | RLS en Supabase |

---

## 🏗️ Arquitectura

```
Users → Cloudflare → Nginx
                   → Nuxt Dashboard (:3000)
                   → FastAPI API     (:8000)
                       ↓
                   Supabase PostgreSQL
                   Redis + Celery Workers
```

### Estructura del Monorepo

```
factura-cr/
├── apps/
│   ├── dashboard/              # Panel SaaS (Nuxt 3)
│   │   ├── pages/
│   │   │   ├── index.vue       # Dashboard financiero
│   │   │   ├── invoices/       # Gestión facturas
│   │   │   ├── clients/        # Gestión clientes
│   │   │   ├── products/       # Catálogo productos
│   │   │   ├── reports/        # Reportes IVA
│   │   │   ├── settings/       # Config empresa
│   │   │   └── auth/login.vue
│   │   └── components/
│   │       ├── InvoiceForm.vue  # Form con CABYS / IVA
│   │       ├── StatsCards.vue
│   │       └── RevenueChart.vue
│   └── web/                    # Landing page
├── services/
│   ├── api/                    # FastAPI backend
│   │   ├── main.py
│   │   ├── routers/            # auth, clients, products, invoices, hacienda
│   │   ├── services/           # hacienda_service, pdf_service
│   │   └── tasks.py            # Celery workers
│   └── hacienda/               # Microservicio Hacienda CR
│       ├── clave.py            # Clave 50 dígitos
│       ├── xml_generator.py    # XML v4.4 FE/TE/NC/ND
│       ├── signer.py           # XAdES-BES signing
│       ├── api_client.py       # OAuth2 + API client
│       ├── hacienda.py         # Pipeline orchestrator
│       ├── auth_service.py     # Token management
│       ├── send_invoice.py     # POST /recepcion
│       ├── check_status.py     # GET /recepcion/{clave}
│       ├── xml/
│       │   └── factura_xml.py  # XML facade
│       ├── signing/
│       │   └── xades_signer.py # XadesSigner class
│       └── utils/
│           ├── base64_encoder.py
│           └── clave_generator.py
├── database/
│   └── schema.sql              # PostgreSQL + RLS
├── infra/
│   ├── docker/                 # Dockerfiles
│   └── nginx/                  # nginx.conf
├── docker-compose.yml
└── Makefile
```

---

## 🚀 Inicio Rápido

### 1. Clonar y configurar

```bash
git clone https://github.com/zonasurtech/factura-cr
cd factura-cr

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

### 2. Backend (FastAPI)

```bash
cd services/api
pip install -r requirements.txt

# Desarrollo
uvicorn main:app --reload --port 8000

# Celery Worker
celery -A tasks worker --loglevel=info

# Celery Beat (tareas programadas)
celery -A tasks beat --loglevel=info
```

### 3. Dashboard (Nuxt 3)

```bash
cd apps/dashboard
pnpm install
pnpm dev    # → http://localhost:3000
```

### 4. Landing (Nuxt 3)

```bash
cd apps/web
pnpm install
pnpm dev    # → http://localhost:3001
```

### 5. Docker Compose (Recomendado)

```bash
docker-compose up --build
```

Servicios levantados:
- **Frontend**: http://localhost:3000
- **API**:      http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Landing**:  http://localhost:3001

---

## ⚙️ Variables de Entorno

Copia `.env.example` → `.env` y configura:

```env
# Base de datos (Supabase)
DATABASE_URL=postgresql+asyncpg://user:pass@db.supabase.co:5432/postgres
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_ANON_KEY=...

# JWT
SECRET_KEY=cambia-esta-clave-en-produccion
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Hacienda CR (Sandbox o Producción)
HACIENDA_ENV=sandbox
HACIENDA_USERNAME=usuario@atv.hacienda.go.cr
HACIENDA_PASSWORD=tu_contraseña_atv

# Certificado BCCR (opcional para sandbox)
BCCR_P12_PATH=/certs/bccr.p12
BCCR_P12_PASSWORD=contraseña_p12

# Redis
REDIS_URL=redis://localhost:6379/0
```

---

## 📋 Clave Hacienda v4.4 — Explicación

La clave de 50 dígitos tiene esta estructura exacta:

```
[506][DDMMAA][CCCCCCCCCCCC][NNNNNNNNNNNNNNNNNNNN][S][XXXXXXXX]
  ↑      ↑          ↑                ↑             ↑       ↑
 País  Fecha(6) Cédula(12)   Consecutivo(20)   Sit(1)  Seg(8)
```

**Consecutivo (20 dígitos):**
```
[SSS][TTT][TT][NNNNNNNNNN]
  ↑    ↑   ↑       ↑
Suc Terminal Tipo  Número(10)
```

Tipos de comprobante:
- `01` = Factura Electrónica (FE)
- `02` = Nota de Débito (ND)
- `03` = Nota de Crédito (NC)
- `04` = Tiquete Electrónico (TE)

Situación:
- `1` = Normal
- `2` = Contingencia
- `3` = Sin Internet

---

## 🔐 API Endpoints

### Autenticación
```
POST /auth/register   → Crear empresa
POST /auth/login      → JWT token
```

### Facturas
```
GET  /invoices          → Listar facturas
POST /invoices          → Crear factura
GET  /invoices/{id}     → Detalle factura
POST /invoices/{id}/send   → Enviar a Hacienda
GET  /invoices/{id}/status → Consultar estado
GET  /invoices/{id}/pdf    → Descargar PDF
GET  /invoices/stats       → Estadísticas dashboard
```

### Clientes y Productos
```
GET/POST/PUT/DELETE /clients
GET/POST/PUT/DELETE /products
```

---

## 🌐 API Hacienda CR — Sandbox

| Servicio | URL |
|---------|-----|
| OAuth2 Token | `https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token` |
| Recepción | `https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1/recepcion` |
| Estado | `https://api-sandbox.comprobanteselectronicos.go.cr/recepcion/v1/recepcion/{clave}` |
| CABYS | `https://api.hacienda.go.cr/fe/cabys` |
| Tipo Cambio | `https://api.hacienda.go.cr/indicadores/tc` |

**Client ID Sandbox:** `api-stag`  
**Client ID Producción:** `api-prod`

---

## 📄 IVA — Tarifas Costa Rica

| Tarifa | Código | Aplicación |
|--------|--------|-----------|
| 13% | `08` | Tarifa general |
| 8%  | `04` | Restaurantes, seguros privados |
| 4%  | `03` | Boletos aéreos, servicios médicos |
| 2%  | `02` | Canasta básica gravada |
| 1%  | `01` | Tarifa reducida |
| 0%  | `07` | Exento |

---

## 🔧 Stack Tecnológico

**Backend:** FastAPI 0.110 · Python 3.11 · SQLAlchemy 2 · Pydantic 2  
**Frontend:** Nuxt 3 · Vue 3 · Nuxt UI · TailwindCSS · Chart.js  
**DB:** Supabase (PostgreSQL) · Redis  
**Workers:** Celery 5 · Redis broker  
**Firma:** cryptography · XAdES-BES · .p12 BCCR  
**PDF:** ReportLab · qrcode  
**Infra:** Docker · Nginx · Cloudflare  

---

## 📖 Referencias Oficiales

- [Estructuras Hacienda CR v4.4](https://www.hacienda.go.cr/docs/Anexosyestructuras.pdf)
- [API Comprobantes Electrónicos](https://www.hacienda.go.cr/docs/ComprobantesElectronicosAPI.html)
- [ATV — Administración Tributaria Virtual](https://atv.hacienda.go.cr)
- [Portal Verificación Hacienda](https://www.hacienda.go.cr/consultahacienda)

---

Desarrollado por **Zona Sur Tech** · Costa Rica 🇨🇷
