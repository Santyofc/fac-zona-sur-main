#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Script de Inicialización — Factura CR con Neon
# ═══════════════════════════════════════════════════════════════

set -e

echo "🚀 Iniciando configuración de Factura CR con Neon..."

# ─── Verificar variables de entorno ────────────────────────────
echo "📋 Verificando configuración..."

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL no está configurada"
    exit 1
fi

echo "✅ Variables de entorno verificadas"

# ─── Esperar a que la base de datos esté lista ─────────────────
echo "⏳ Esperando conexión a Neon..."
sleep 5

# ─── Ejecutar migraciones ─────────────────────────────────────
echo "📦 Ejecutando migraciones de base de datos..."

# Crear tablas base
python -c "
import asyncio
import sys
import os
sys.path.append('/app')

from database import create_tables

async def init_db():
    try:
        await create_tables()
        print('✅ Tablas creadas exitosamente')
    except Exception as e:
        print(f'❌ Error creando tablas: {e}')
        raise

asyncio.run(init_db())
"

# ─── Ejecutar migraciones de Prisma (si existen) ──────────────
if [ -d "/app/packages/db/prisma" ]; then
    echo "📦 Ejecutando migraciones de Prisma..."
    cd /app/packages/db
    if command -v npx &> /dev/null; then
        npx prisma migrate deploy
        npx prisma generate
    else
        echo "⚠️  npx no encontrado, saltando migraciones de Prisma"
    fi
    cd /app
fi

# ─── Crear datos de prueba ────────────────────────────────────
echo "🎭 Creando datos de prueba..."

python -c "
import asyncio
import sys
sys.path.append('/app')

from database import get_db_session
from models.models import Company, User
from datetime import datetime
import os

async def create_test_data():
    try:
        async with get_db_session() as db:
            # Verificar si ya existe una empresa de prueba
            result = await db.execute('SELECT COUNT(*) FROM companies')
            count = result.scalar()
            
            if count == 0:
                print('Creando empresa de prueba...')
                
                # Crear empresa de prueba
                company = Company(
                    name='Empresa de Prueba CR',
                    trade_name='Test Company',
                    cedula_type='JURIDICA',
                    cedula_number='3101234567',
                    email='test@empresa.cr',
                    phone='2222-3333',
                    address='San José, Costa Rica',
                    plan='free',
                    is_active=True
                )
                db.add(company)
                await db.commit()
                await db.refresh(company)
                
                # Crear usuario admin
                user = User(
                    company_id=company.id,
                    email='admin@test.cr',
                    full_name='Admin Test',
                    hashed_password='$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeCt1uLj.zpvkgUqO',  # 'password'
                    role='admin',
                    is_active=True
                )
                db.add(user)
                await db.commit()
                
                print(f'✅ Empresa creada: {company.name}')
                print(f'✅ Usuario admin: admin@test.cr / password')
            else:
                print('ℹ️  Datos de prueba ya existen')
    except Exception as e:
        print(f'❌ Error creando datos de prueba: {e}')
        raise

asyncio.run(create_test_data())
"

# ─── Verificar conexión ───────────────────────────────────────
echo "🔍 Verificando conexión a la base de datos..."

python -c "
import asyncio
import sys
sys.path.append('/app')

from database import get_db_session

async def test_connection():
    try:
        async with get_db_session() as db:
            result = await db.execute('SELECT version()')
            version = result.scalar()
            print(f'✅ Conexión exitosa a Neon')
            print(f'📊 PostgreSQL versión: {version.split()[1]}')
    except Exception as e:
        print(f'❌ Error de conexión: {e}')
        exit(1)

asyncio.run(test_connection())
"

# ─── Configurar Supabase Storage (si se usa) ──────────────────
if [ -n "$SUPABASE_URL" ] && [ -n "$SUPABASE_SERVICE_ROLE_KEY" ]; then
    echo "📦 Configurando Supabase Storage..."
    
    python -c "
import os
import sys
sys.path.append('/app')

try:
    from supabase import create_client
    
    supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
    
    # Verificar si el bucket 'invoices' existe
    buckets = supabase.storage.list_buckets()
    bucket_names = [b['name'] for b in buckets]
    
    if 'invoices' not in bucket_names:
        print('⚠️  Asegúrate de crear el bucket invoices en Supabase manualmente')
        print('   Ve a: https://supabase.com/dashboard/project/YOUR_PROJECT/storage')
    else:
        print('✅ Bucket invoices encontrado')
        
except Exception as e:
    print(f'⚠️  No se pudo verificar Supabase: {e}')
"
fi

echo ""
echo "🎉 ¡Factura CR está listo!"
echo ""
echo "📱 Dashboard: http://localhost:3000"
echo "🔗 API Docs: http://localhost:8000/docs"
echo "👤 Usuario de prueba: admin@test.cr / password"
echo ""
echo "📋 Próximos pasos:"
echo "1. Configurar credenciales reales en .env"
echo "2. Subir certificado .p12 a services/api/certs/"
echo "3. Probar crear una factura"
echo "4. Verificar envío a Hacienda (sandbox)"
echo ""
echo "🚀 ¡Todo funcionando!"