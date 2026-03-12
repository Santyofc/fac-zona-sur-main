# ============================================================
# Factura CR — Makefile
# Comandos rápidos para desarrollo y producción
# ============================================================

.PHONY: help dev dev-api dev-dashboard install build \
        docker-up docker-down docker-build migrate clean

# Comando por defecto
help:
	@echo ""
	@echo "  ⚡ Factura CR — Comandos disponibles:"
	@echo ""
	@echo "  make install       — Instalar todas las dependencias"
	@echo "  make dev           — Iniciar dashboard (Nuxt)"
	@echo "  make dev-api       — Iniciar API (FastAPI + uvicorn)"
	@echo "  make dev-worker    — Iniciar Celery worker"
	@echo "  make docker-up     — Levantar toda la infraestructura"
	@echo "  make docker-down   — Detener contenedores"
	@echo "  make docker-build  — Rebuild imágenes Docker"
	@echo "  make migrate       — Aplicar schema SQL en base de datos"
	@echo "  make clean         — Limpiar archivos temporales"
	@echo ""

# ─── Instalación ─────────────────────────────────────────────
install:
	@echo "📦 Instalando dependencias frontend..."
	pnpm install
	@echo "🐍 Instalando dependencias Python..."
	cd services/api && pip install -r requirements.txt

# ─── Desarrollo ──────────────────────────────────────────────
dev:
	cd apps/dashboard && pnpm dev

dev-web:
	cd apps/web && pnpm dev

dev-api:
	cd services/api && uvicorn main:app --reload --port 8000 --log-level info

dev-worker:
	cd services/api && celery -A tasks worker --loglevel=info --concurrency=2

dev-beat:
	cd services/api && celery -A tasks beat --loglevel=info

dev-all:
	@echo "🚀 Iniciando todos los servicios en paralelo..."
	$(MAKE) -j4 dev dev-api dev-worker

# ─── Build ───────────────────────────────────────────────────
build:
	pnpm build

# ─── Docker ──────────────────────────────────────────────────
docker-up:
	docker-compose up -d
	@echo "✅ Servicios iniciados:"
	@echo "   Frontend:  http://localhost:3000"
	@echo "   API:       http://localhost:8000"
	@echo "   API Docs:  http://localhost:8000/docs"
	@echo "   Redis:     localhost:6379"

docker-down:
	docker-compose down

docker-build:
	docker-compose build --no-cache

docker-logs:
	docker-compose logs -f

docker-ps:
	docker-compose ps

# ─── Base de Datos ───────────────────────────────────────────
migrate:
	@echo "🗄️  Aplicando schema SQL en Supabase / PostgreSQL..."
	psql $(DATABASE_URL) -f database/schema.sql

migrate-seed:
	psql $(DATABASE_URL) -f database/migrations/001_initial.sql

# ─── Limpieza ────────────────────────────────────────────────
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".nuxt" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".output" -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "🧹 Limpieza completada"
