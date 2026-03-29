# 🔧 GUÍA DE IMPLEMENTACIÓN INMEDIATA

**Prioridad:** Para que la aplicación sea funcional, enfoca en estos 5 items en este orden

---

## ⚡ TOP 5 COSAS A ARREGLAR AHORA

### 1. **CELERY WORKERS NO EJECUTAN TAREAS** (30 min)

**Problema:** Las facturas se envían a "processing" pero nunca se actualizan

**Ubicación:** [services/api/tasks.py](services/api/tasks.py)

**Qué hacer:**
```python
# ACTUALMENTE EN tasks.py línea 52-80:
async def _async_process_invoice(invoice_id: str, config) -> dict:
    """Esta función NO hace nada real"""
    # Necesita:
    # 1. Llamar InvoiceHaciendaService.process_invoice()
    # 2. Actualizar DB con resultado
    # 3. Registrar logs
```

**Solución:** Implementar la función `_async_process_invoice()` que actualmente está stub:

```python
async def _async_process_invoice(invoice_id: str, config) -> dict:
    from services.invoice_hacienda_service import InvoiceHaciendaService
    from database import AsyncSessionLocal
    
    db = AsyncSessionLocal()
    service = InvoiceHaciendaService(db, config)
    result = await service.process_invoice(invoice_id)
    await db.close()
    return result
```

**Impacto:** ✅ Las facturas se procesarán automáticamente en background

---

### 2. **DASHBOARD STATS NO CARGAN DATOS** (20 min)

**Problema:** Las tarjetas muestran "undefined" o valores hardcodeados

**Ubicación:** [apps/dashboard/pages/index.vue](apps/dashboard/pages/index.vue)

**Qué está mal:**
```vue
<!-- Línea 39: statusBreakdown nunca se asigna -->
<div v-for="item in statusBreakdown" :key="item.label">

<!-- Necesita montar el composable-->
const { fetchStats } = useInvoices()

onMounted(async () => {
  stats.value = await fetchStats()  // ← Esto NO se ejecuta
})
```

**Solución rápida (20 líneas):**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useInvoices } from '~/composables/useInvoices'

const stats = ref(null)
const statsLoading = ref(false)
const { fetchStats } = useInvoices()

onMounted(async () => {
  statsLoading.value = true
  try {
    stats.value = await fetchStats()
  } catch (e) {
    console.error('Error cargando stats:', e)
  } finally {
    statsLoading.value = false
  }
})

// Computar statusBreakdown desde stats.value
const statusBreakdown = computed(() => {
  if (!stats.value) return []
  return [
    { label: 'Aceptadas', count: stats.value.invoices_accepted, dotClass: 'bg-green-500' },
    { label: 'Pendientes', count: stats.value.invoices_pending, dotClass: 'bg-yellow-500' },
    { label: 'Rechazadas', count: stats.value.invoices_rejected, dotClass: 'bg-red-500' },
  ]
})
</script>
```

**Impacto:** ✅ Dashboard muestra números reales

---

### 3. **SUPABASE STORAGE PARA PDFs** (1 hora)

**Problema:** `pdf_url` siempre es NULL, no se pueden descargar facturas

**Ubicación:** [services/api/services/hacienda_service.py](services/api/services/hacienda_service.py#L158)

**Qué hacer:**

```python
# Después de línea 120 (después de firmar XML)
# Agregar:

async def _upload_pdf_to_storage(pdf_bytes: bytes, invoice_id: str, clave: str):
    """Sube PDF a Supabase Storage"""
    from supabase import create_client
    import os
    
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    
    filename = f"invoices/{invoice_id}/{clave}.pdf"
    response = supabase.storage.from_("invoices").upload(filename, pdf_bytes)
    
    # Generar URL pública
    signed_url = supabase.storage.from_("invoices").get_public_url(filename)
    return signed_url

# En process_invoice_to_hacienda(), después de generar PDF:
pdf_service.generate_invoice_pdf(invoice_data)
pdf_url = await _upload_pdf_to_storage(pdf_bytes, invoicer_id, clave)
hacienda_doc.pdf_url = pdf_url
```

**Impacto:** ✅ Usuarios pueden descargar facturas en PDF

---

### 4. **PAYPAL INTEGRATION REAL** (2-3 horas)

**Problema:** Botón "Pagar con PayPal" devuelve order_id FALSO

**Ubicación:** [services/api/routers/payments.py](services/api/routers/payments.py#L45-L70)

**Qué hacer:**

```python
import httpx

async def get_paypal_access_token() -> str:
    """Obtiene token REAL de PayPal"""
    auth = (settings.PAYPAL_CLIENT_ID, settings.PAYPAL_SECRET)
    data = {"grant_type": "client_credentials"}
    
    url = "https://api-m.sandbox.paypal.com/v1/oauth2/token"  # O production
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, auth=auth, data=data, timeout=10)
        if resp.status_code != 200:
            raise Exception(f"PayPal auth failed: {resp.text}")
        return resp.json()["access_token"]

@router.post("/paypal/create", response_model=dict)
async def create_paypal_order(
    request: PayPalOrderRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Crea orden REAL en PayPal"""
    amount_per_month = 19.99
    total_amount = amount_per_month * request.months
    
    access_token = await get_paypal_access_token()
    
    url = "https://api-m.sandbox.paypal.com/v2/checkout/orders"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "USD",
                "value": str(total_amount)
            },
            "reference_id": str(current_user.company_id)
        }],
        "return_url": f"{settings.FRONTEND_URL}/settings/billing?status=success",
        "cancel_url": f"{settings.FRONTEND_URL}/settings/billing?status=cancel"
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, headers=headers, json=payload, timeout=10)
        if resp.status_code == 201:
            order = resp.json()
            # Guardar intención en DB
            payment = Payment(
                company_id=current_user.company_id,
                amount=total_amount,
                currency="USD",
                payment_method=PaymentMethod.PAYPAL,
                reference_id=order["id"],
                status=PaymentStatus.PENDING,
                months_added=request.months
            )
            db.add(payment)
            await db.commit()
            
            return {"order_id": order["id"], "status": "pending"}
        else:
            raise HTTPException(status_code=500, detail=f"PayPal error: {resp.text}")
```

**Impacto:** ✅ Pagos reales procesados en sandbox/production

---

### 5. **LISTAR FACTURAS CON DATOS REALES** (45 min)

**Problema:** [apps/dashboard/pages/invoices/index.vue](apps/dashboard/pages/invoices/index.vue) no ejecuta fetch

**Qué hacer:**

En la página, agregar:

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useInvoices } from '~/composables/useInvoices'

const invoices = ref([])
const loading = ref(false)
const { fetchInvoices } = useInvoices()

onMounted(async () => {
  loading.value = true
  try {
    invoices.value = await fetchInvoices({ limit: 50 })
  } catch (e) {
    console.error('Error:', e)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div>
    <!-- Filtros existentes... -->
    
    <!-- Tabla -->
    <InvoiceTable 
      :invoices="invoices" 
      :loading="loading"
      @reload="loadInvoices"
    />
  </div>
</template>
```

**Impacto:** ✅ Usuarios ven sus facturas reales

---

## 📊 VERIFICACIÓN POST-IMPLEMENTACIÓN

Después de los 5 cambios, ejecuta:

```bash
# 1. Verificar que Celery worker inicia
cd services/api
celery -A tasks worker --loglevel=info

# 2. Verificar endpoints en Swagger
curl http://localhost:8000/docs

# 3. Verificar conexión a Supabase
python -c "from supabase import create_client; create_client('...', '...')"

# 4. Enviar factura de prueba
curl -X POST http://localhost:8000/invoices/{id}/send \
  -H "Authorization: Bearer {token}"

# 5. Verificar en dashboard
# - Stats cargan
# - Facturas aparecen
# - PDF descargable
```

---

## ⚙️ CONFIGURACION FALTANTE

### Archivo `.env` necesario en `services/api/`:

```env
# Base de datos
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/factura_cr
REDIS_URL=redis://localhost:6379/0

# Hacienda CR
HACIENDA_USERNAME=usuario_atv
HACIENDA_PASSWORD=contraseña_atv
HACIENDA_ENV=sandbox  # o production

# PayPal
PAYPAL_CLIENT_ID=...
PAYPAL_SECRET=...

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...

# JWT
JWT_SECRET=random-key-here
JWT_ALGORITHM=HS256

# Frontend URL (para OAuth redirect)
FRONTEND_URL=http://localhost:3000
```

### Variables en `apps/dashboard/.env.local`:

```env
NUXT_PUBLIC_API_BASE=http://localhost:8000
NUXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NUXT_PUBLIC_SUPABASE_KEY=...
```

---

## 🐳 PASOS RÁPIDOS PARA LEVANTAR TODO

```bash
# 1. Base de datos + Redis
docker-compose up -d postgres redis

# 2. Migraciones
docker exec factura-cr-postgres psql -U postgres -d factura_cr -f /database/schema.sql

# 3. Backend
cd services/api
pip install -r requirements.txt
uvicorn main:app --reload

# 4. Celery (en otro terminal)
celery -A tasks worker --loglevel=info

# 5. Frontend
cd apps/dashboard
npm run dev

# 6. Visitar
# Dashboard: http://localhost:3000
# API Docs: http://localhost:8000/docs
```

---

**Tiempo estimado:** 4-5 horas para todo  
**Impacto:** MVP funcional 60% → 85% completitud
