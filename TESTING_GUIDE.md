# 🧪 GUÍA DE TESTING & VERIFICACIÓN

## ✅ CHECKLIST DE VERIFICATION

Usa esto para verificar qué funciona y qué no en tu instancia local

```bash
# Supone que tienes:
# - Backend en http://localhost:8000
# - Frontend en http://localhost:3000
# - PostgreSQL en localhost:5432
# - Redis en localhost:6379
```

---

## 1️⃣ TEST: Backend Health

```bash
# ¿Está corriendo el API?
curl -X GET http://localhost:8000/health

# Respuesta esperada:
# {"status": "ok"}

# ¿Está el Swagger disponible?
curl -X GET http://localhost:8000/docs

# Respuesta: HTML (≥ 200 caracteres)
```

---

## 2️⃣ TEST: Database Connection

```bash
# ¿Conecta a PostgreSQL?
curl -X GET http://localhost:8000/invoices \
  -H "Authorization: Bearer fake-token"

# Si funciona: 401 (Unauthorized) ✅
# Si falla: 500 (Connection Error) ❌

# Conectar directamente a DB:
psql -U postgres -h localhost -d factura_cr

\dt  # Ver todas las tablas
SELECT COUNT(*) FROM companies;  # Ver si hay datos
```

---

## 3️⃣ TEST: Authentication

```bash
# Registrar nueva empresa
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456",
    "full_name": "Test User",
    "company_name": "Test Corp",
    "company_cedula": "3-101-123456",
    "company_cedula_type": "JURIDICA"
  }'

# Respuesta esperada (200):
# {
#   "access_token": "eyJ0eXAi...",
#   "token_type": "bearer",
#   "expires_in": 1440,
#   "user_id": "uuid",
#   "company_id": "uuid"
# }

# Si falla: 400 (Email ya existe)
# Entonces usar login:

curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123456"
  }'

# Copiar el access_token para próximas requestsN
TOKEN="eyJ0eXAi..."
```

---

## 4️⃣ TEST: CRUD de Clientes

```bash
TOKEN="eyJ0eXAi..."

# Crear cliente
curl -X POST http://localhost:8000/clients \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Cliente",
    "cedula_type": "FISICA",
    "cedula_number": "1-234-567890",
    "email": "cliente@example.com",
    "province": "San José",
    "canton": "San José",
    "district": "Centro"
  }'

# Respuesta (201):
# { "id": "uuid", "name": "Mi Cliente", ... }

CLIENT_ID="uuid-del-cliente"

# Listar clientes
curl -X GET http://localhost:8000/clients \
  -H "Authorization: Bearer $TOKEN"

# Obtener cliente específico
curl -X GET http://localhost:8000/clients/$CLIENT_ID \
  -H "Authorization: Bearer $TOKEN"

# Actualizar cliente
curl -X PUT http://localhost:8000/clients/$CLIENT_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mi Cliente Actualizado"
  }'
```

---

## 5️⃣ TEST: Crear Factura

```bash
TOKEN="eyJ0eXAi..."
CLIENT_ID="uuid-del-cliente"

# Crear producto primero
curl -X POST http://localhost:8000/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Servicio de Consultoría",
    "unit_price": 10000.00,
    "tax_rate": 13.0,
    "currency": "CRC"
  }'

# Respuesta:
# { "id": "uuid", "name": "Servicio...", ... }

PRODUCT_ID="uuid-del-producto"

# Crear factura
curl -X POST http://localhost:8000/invoices \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "'$CLIENT_ID'",
    "doc_type": "FE",
    "currency": "CRC",
    "sale_condition": "01",
    "payment_method": "01",
    "items": [
      {
        "line_number": 1,
        "description": "Servicio de Consultoría",
        "quantity": 1,
        "unit_price": 10000,
        "tax_rate": 13.0,
        "cabys_code": "9999999999999"
      }
    ]
  }'

# Respuesta (201):
# {
#   "id": "invoice-uuid",
#   "consecutive": "00100001010000000001",
#   "status": "draft",
#   "total": 11300,
#   ...
# }

INVOICE_ID="invoice-uuid"
```

---

## 6️⃣ TEST: Enviar a Hacienda ⭐ CRÍTICO

```bash
TOKEN="eyJ0eXAi..."
INVOICE_ID="invoice-uuid"

# Enviar factura (inicia background task)
curl -X POST http://localhost:8000/invoices/$INVOICE_ID/send \
  -H "Authorization: Bearer $TOKEN"

# Respuesta (200):
# {
#   "invoice_id": "...",
#   "status": "processing",
#   "hacienda_status": "procesando",
#   "hacienda_msg": "Factura en procesamiento..."
# }

# ⚠️ SI ESTO FALLA: Los workers no están corriendo
# En otro terminal:
cd services/api
celery -A tasks worker --loglevel=info

# Una vez que el worker esté corriendo:

# Consultar estado (cada 5 segundos)
curl -X GET http://localhost:8000/invoices/$INVOICE_ID/status \
  -H "Authorization: Bearer $TOKEN"

# Esperado (después de 10-30 segundos):
# {
#   "status": "accepted",
#   "hacienda_status": "aceptado",
#   "clave": "50 dígitos aquí",
#   "pdf_url": "..."
# }

# Si sigue "processing" después de 1 min:
# 1. Revisar logs del worker
# 2. Verificar HACIENDA_USERNAME + PASSWORD en .env
# 3. Verificar certificado .p12 existe
```

---

## 7️⃣ TEST: Dashboard Frontend

```
http://localhost:3000

Prueba esto en orden:

1. ¿Carga la página? (no error 404)
   Esperado: "Center of Operations" visible

2. ¿Aparecen las tarjetas de stats?
   Esperado: Números reales (no "undefined")
   Si no: Stats fetch no está implementado

3. ¿Se pobla la tabla de facturas?
   Esperado: Las 3 últimas facturas creadas
   Si no: useInvoices() no se ejecuta en mount

4. ¿Botón "NUEVA FACTURA" funciona?
   Esperado: Abre modal con form
   Si no: Enrutamiento roto

5. ¿Se puede crear factura en UI?
   Esperado: Form submit sin error
   Si falla: Validación o API no conectado
```

---

## 8️⃣ TEST: Celery Workers

```bash
# Terminal 1: Backend
cd services/api
python -m uvicorn main:app --reload

# Terminal 2: Celery Worker
cd services/api
celery -A tasks worker --loglevel=info

# Terminal 3: Celery Beat (tareas programadas)
cd services/api
celery -A tasks beat --loglevel=info

# Verificar que workers reciben tasks:
# Enviar factura desde dashboard (step 6)
# En terminal 2, deberías ver:
# [tasks.send_invoice_to_hacienda] Received task
# [tasks.send_invoice_to_hacienda] Task succeeded

# Si NO ves esto:
# 1. Redis no está corriendo
#    docker run -d -p 6379:6379 redis
#
# 2. CELERY_BROKER_URL en .env es incorrecto
#    Debe ser: redis://localhost:6379/0
#
# 3. Task function vacía (sin ninguna lógica)
#    Necesita implementación en tasks.py
```

---

## 9️⃣ TEST: Database Queries

```bash
# Conectar a DB
psql -U postgres -h localhost -d factura_cr

# Ver todas las compañías
SELECT id, name, email, plan FROM companies;

# Ver facturas creadas
SELECT id, consecutive, status, total FROM invoices;

# Ver clientes
SELECT id, name, cedula_number, email FROM clients;

# Ver estado de documentos Hacienda
SELECT invoice_id, clave, hacienda_status, submission_date 
FROM hacienda_documents;

# Ver pagos
SELECT * FROM payments;

# Query para verificar que foreignkeys funcionan
SELECT i.id, i.consecutive, c.name, u.full_name
FROM invoices i
LEFT JOIN clients c ON i.client_id = c.id
LEFT JOIN users u ON i.created_by = u.id
LIMIT 10;
```

---

## 🔟 TEST: PayPal Integration (Mock)

```bash
TOKEN="eyJ0eXAi..."

# Crear orden PayPal (returns FAKE order_id actualmente)
curl -X POST http://localhost:8000/payments/paypal/create \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"months": 1}'

# Esperado (mock):
# {
#   "order_id": "PAYPAL-MOCK-ORDER-1679661234.5",
#   "amount": 19.99,
#   "currency": "USD"
# }

# Para implementar REAL:
# 1. Reemplazar con PayPal API credentials
# 2. Llamar https://api-m.sandbox.paypal.com/v2/checkout/orders
# 3. Capturar order después de confirmación
# 4. Webhook para confirmación
```

---

## 📊 PERFORMANCE TEST

```bash
# Crear 100 facturas y ver tiempo

TOKEN="eyJ0eXAi..."
CLIENT_ID="uuid"

for i in {1..100}; do
  curl -X POST http://localhost:8000/invoices \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "client_id": "'$CLIENT_ID'",
      "doc_type": "FE",
      "items": [{
        "description": "Item '$i'",
        "quantity": 1,
        "unit_price": 1000,
        "tax_rate": 13.0
      }]
    }' &>/dev/null &
done

wait
echo "Done: 100 facturas creadas"

# Ver cuántas hay:
curl -X GET http://localhost:8000/invoices \
  -H "Authorization: Bearer $TOKEN" | jq '. | length'
```

---

## 🚨 TROUBLESHOOTING

### Problema: "CORS error en frontend"
```
Error: Access to XMLHttpRequest from origin 'http://localhost:3000'
has been blocked by CORS policy

Solución:
1. Verificar ALLOWED_ORIGINS en services/api/config.py
2. Incluir http://localhost:3000
3. Reiniciar backend
```

### Problema: "Token expirado"
```
Error: {"detail": "Could not validate credentials"}

Solución:
1. Re-login en dashboard
2. O verificar JWT_EXPIRE_MINUTES en .env (mínimo 60)
3. No hay refresh token actualmente - necesita nuevas credentials
```

### Problema: "Database connection error"
```
Error: (asyncpg.exceptions.ClientConfigError)

Solución:
1. Verificar PostgreSQL corre: docker ps | grep postgres
2. Verificar credenciales en DATABASE_URL
3. Crear DB si no existe: createdb factura_cr
4. Ejecutar migraciones: psql < database/schema.sql
```

### Problema: "Celery task no ejecuta"
```
Síntoma: Factura en "processing" siempre

Solución:
1. ¿Redis corre? docker ps | grep redis
2. ¿Worker corre? ps aux | grep celery
3. ¿Task function está vacía? Revisar services/api/tasks.py
4. Ver logs: celery -A tasks worker --loglevel=debug
```

### Problema: "PDF no se genera"
```
Error en download PDF o pdf_url es NULL

Solución:
1. Supabase Storage no configurado
2. ReportLab no instalado: pip install reportlab qrcode
3. Certificado .p12 no encontrado en /certs
```

---

## 📋 TEST CHECKLIST (Antes de Deploy)

```
Backend Tests:
[ ] Health endpoint responde 200
[ ] Auth register/login funciona
[ ] CRUD clientes funciona
[ ] CRUD productos funciona  
[ ] Crear factura funciona
[ ] Enviar a Hacienda inicia (status = processing)
[ ] Worker recibe task (logs de Celery)
[ ] Base de datos persiste datos

Frontend Tests:
[ ] Dashboard carga sin errores 404
[ ] Stats cargan números reales (no undefined)
[ ] Tabla de facturas pobla desde API
[ ] Crear factura abre form + puede enviar
[ ] Listar facturas actua desde API
[ ] Crear cliente funciona
[ ] Settings guarda empresa

Integration Tests:
[ ] Factura → Hacienda → Status actualiza (end-to-end)
[ ] PDF descargable después de aceptado
[ ] Pagos reciben webhook (mock)
[ ] Email notificación (si implementado)

Performance:
[ ] Dashboard carga < 2 segundos
[ ] API /invoices responde < 500ms
[ ] Crear factura < 1 segundo
```

---

## 🎯 TESTING CON POSTMAN

Importa esto como Collection:

```json
{
  "info": {
    "name": "FacturaCR API Tests",
    "description": "Tests para endpoints críticos"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://localhost:8000/health"
      }
    },
    {
      "name": "Register User",
      "request": {
        "method": "POST",
        "url": "http://localhost:8000/auth/register",
        "header": [
          { "key": "Content-Type", "value": "application/json" }
        ],
        "body": {
          "raw": "{\"email\":\"test@test.com\",\"password\":\"Test123456\",\"full_name\":\"Test\",\"company_name\":\"Test Corp\",\"company_cedula\":\"3-101-123456\",\"company_cedula_type\":\"JURIDICA\"}"
        }
      }
    }
  ]
}
```

---

**Generado:** 25 de marzo de 2026
