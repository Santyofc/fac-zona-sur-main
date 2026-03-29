#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Script de Inicio Rápido — Factura CR
# ═══════════════════════════════════════════════════════════════

set -e

echo "🚀 Iniciando Factura CR..."

# ─── Verificar Docker ──────────────────────────────────────────
if ! command -v docker &> /dev/null; then
    echo "❌ Docker no está instalado"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose no está instalado"
    exit 1
fi

# ─── Verificar .env ────────────────────────────────────────────
if [ ! -f ".env" ]; then
    echo "📋 Creando .env desde .env.example..."
    cp .env.example .env
    echo "⚠️  Edita el archivo .env con tus credenciales reales antes de continuar"
    echo "   - DATABASE_URL (Neon)"
    echo "   - SUPABASE_* (Storage)"
    echo "   - PAYPAL_* (Pagos)"
    echo "   - HACIENDA_* (API Costa Rica)"
    echo ""
    read -p "¿Has configurado el .env? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "⚠️  Configura el .env y vuelve a ejecutar este script"
        exit 1
    fi
fi

# ─── Instalar dependencias ─────────────────────────────────────
echo "📦 Instalando dependencias..."
pnpm install

# ─── Construir imágenes ────────────────────────────────────────
echo "🏗️  Construyendo imágenes Docker..."
docker-compose build

# ─── Inicializar base de datos ────────────────────────────────
echo "🗄️  Inicializando base de datos..."
docker-compose --profile init run --rm init-db

# ─── Iniciar servicios ─────────────────────────────────────────
echo "▶️  Iniciando servicios..."
docker-compose up -d

# ─── Verificar servicios ───────────────────────────────────────
echo "🔍 Verificando servicios..."
sleep 10

if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "🎉 ¡Factura CR está ejecutándose!"
    echo ""
    echo "📱 Dashboard: http://localhost:3000"
    echo "🔗 API Docs: http://localhost:8000/docs"
    echo "👤 Usuario de prueba: admin@test.cr / password"
    echo ""
    echo "📋 Comandos útiles:"
    echo "  docker-compose logs -f          # Ver logs en tiempo real"
    echo "  docker-compose ps               # Ver estado de servicios"
    echo "  docker-compose restart backend  # Reiniciar backend"
    echo "  docker-compose down             # Detener todo"
    echo ""
    echo "🚀 ¡Todo listo!"
else
    echo "❌ Error: Los servicios no se iniciaron correctamente"
    echo "Ejecuta: docker-compose logs"
    exit 1
fi