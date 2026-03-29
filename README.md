# ═══════════════════════════════════════════════════════════════
# Factura CR — Sistema de Facturación Electrónica Costa Rica
# ═══════════════════════════════════════════════════════════════

Sistema completo de facturación electrónica para Costa Rica con integración a Hacienda, PayPal y Neon PostgreSQL.

## 🚀 Inicio Rápido con Neon

### 1. Configurar Neon Database

1. Ve a [neon.tech](https://neon.tech) y crea una cuenta
2. Crea un nuevo proyecto
3. Copia la connection string (parece: `postgresql://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require`)
4. Actualiza tu `.env`:

```bash
# Reemplaza con tu connection string real
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require
ASYNC_DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx.us-east-1.aws.neon.tech/neondb?sslmode=require

# Opcional: Para usar Neon API (backups, etc.)
NEON_PROJECT_ID=tu-project-id
NEON_API_KEY=tu-api-key
```

### 2. Configurar Supabase (Storage)

1. Ve a [supabase.com](https://supabase.com) y crea un proyecto
2. Ve a Settings > API y copia:
   - Project URL
   - Anon public key
   - Service role key (secret!)
3. Crea un bucket llamado `invoices` con permisos públicos
4. Actualiza tu `.env`:

```bash
SUPABASE_URL=https://tu-project.supabase.co
SUPABASE_ANON_KEY=tu-anon-key
SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key
```

### 3. Configurar PayPal

1. Ve a [developer.paypal.com](https://developer.paypal.com)
2. Crea una app en sandbox
3. Copia Client ID y Secret
4. Actualiza tu `.env`:

```bash
PAYPAL_CLIENT_ID=tu-client-id
PAYPAL_CLIENT_SECRET=tu-secret
PAYPAL_ENVIRONMENT=sandbox  # o 'production'
```

### 4. Configurar Hacienda (Sandbox)

1. Regístrate en [Hacienda ATV](https://www.hacienda.go.cr/ATV/Inicio.aspx)
2. Obtén credenciales de API
3. Descarga certificado .p12
4. Actualiza tu `.env`:

```bash
HACIENDA_CLIENT_ID=tu-client-id
HACIENDA_CLIENT_SECRET=tu-secret
HACIENDA_USERNAME=tu-cedula
HACIENDA_PASSWORD=tu-atv-password
```

5. Copia certificado a: `services/api/certs/firma.p12`

### 5. Iniciar la aplicación

```bash
# Instalar dependencias
pnpm install

# Construir imágenes Docker
docker-compose build

# Inicializar base de datos (solo primera vez)
docker-compose --profile init run --rm init-db

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f
```

### 6. Acceder a la aplicación

- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Usuario de prueba**: admin@test.cr / password

## 📋 Arquitectura

```
Factura CR
├── Frontend (Nuxt 3 + Vue 3 + Tailwind)
├── Backend (FastAPI + PostgreSQL)
├── Workers (Celery + Redis)
├── Storage (Supabase)
├── Payments (PayPal)
└── Hacienda API (Costa Rica)
```

## 🔧 Desarrollo Local

### Prerrequisitos

- Docker & Docker Compose
- Node.js 18+ & pnpm
- Python 3.11+
- Cuentas en Neon, Supabase, PayPal, Hacienda

### Comandos útiles

```bash
# Desarrollo frontend
cd apps/dashboard
pnpm dev

# Desarrollo backend
cd services/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Ver estado de contenedores
docker-compose ps

# Ver logs
docker-compose logs backend
docker-compose logs worker

# Reiniciar servicios
docker-compose restart backend
docker-compose restart worker

# Limpiar todo
docker-compose down -v
```

## 🔐 Variables de Entorno

Ver `.env.example` para todas las variables requeridas.

## 📊 Base de Datos

### Esquema principal

- `companies` - Empresas registradas
- `users` - Usuarios del sistema
- `clients` - Clientes de las empresas
- `products` - Productos/servicios
- `invoices` - Facturas electrónicas
- `invoice_items` - Items de facturas
- `payments` - Pagos registrados

### Migraciones

Las migraciones se ejecutan automáticamente al iniciar con Docker.

## 🚀 Despliegue en Producción

### 1. Configurar dominio

```bash
# Actualizar .env
ALLOWED_ORIGINS=https://tu-dominio.com
FRONTEND_URL=https://tu-dominio.com
```

### 2. SSL con Let's Encrypt

```bash
# Instalar certbot
sudo apt install certbot

# Obtener certificado
sudo certbot certonly --standalone -d tu-dominio.com

# Copiar certificados
sudo cp /etc/letsencrypt/live/tu-dominio.com/fullchain.pem infra/nginx/ssl/
sudo cp /etc/letsencrypt/live/tu-dominio.com/privkey.pem infra/nginx/ssl/
```

### 3. Configurar Nginx

Actualizar `infra/nginx/nginx.conf` con tu dominio.

### 4. Cambiar a producción

```bash
# En .env
PAYPAL_ENVIRONMENT=production
HACIENDA_API_URL=https://api.comprobanteselectronicos.go.cr/recepcion/v1
HACIENDA_TOKEN_URL=https://idp.comprobanteselectronicos.go.cr/auth/realms/rut/protocol/openid-connect/token
```

## 🧪 Testing

```bash
# Ejecutar tests
docker-compose exec backend python -m pytest

# Test de integración Hacienda
python visual_test_hacienda.py

# Test de polling
python test_polling.py
```

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/zonasurtech/factura-cr/issues)
- **Docs**: Ver carpeta `docs/`
- **Comunidad**: [Discord/Slack de Zona Sur Tech]

## 📄 Licencia

MIT License - ver LICENSE para más detalles.

---

**Desarrollado por [Zona Sur Tech Hub](https://zonasurtech.online)**
