@echo off
REM ═══════════════════════════════════════════════════════════════
REM Script de Inicio Rápido — Factura CR (Windows)
REM ═══════════════════════════════════════════════════════════════

echo 🚀 Iniciando Factura CR...

REM ─── Verificar Docker ──────────────────────────────────────────
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker no está instalado
    pause
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose no está instalado
    pause
    exit /b 1
)

REM ─── Verificar .env ────────────────────────────────────────────
if not exist ".env" (
    echo 📋 Creando .env desde .env.example...
    copy .env.example .env
    echo ⚠️  Edita el archivo .env con tus credenciales reales antes de continuar
    echo    - DATABASE_URL (Neon)
    echo    - SUPABASE_* (Storage)
    echo    - PAYPAL_* (Pagos)
    echo    - HACIENDA_* (API Costa Rica)
    echo.
    set /p choice="¿Has configurado el .env? (y/N): "
    if /i not "!choice!"=="y" (
        echo ⚠️  Configura el .env y vuelve a ejecutar este script
        pause
        exit /b 1
    )
)

REM ─── Instalar dependencias ─────────────────────────────────────
echo 📦 Instalando dependencias...
pnpm install

REM ─── Construir imágenes ────────────────────────────────────────
echo 🏗️  Construyendo imágenes Docker...
docker-compose build

REM ─── Inicializar base de datos ────────────────────────────────
echo 🗄️  Inicializando base de datos...
docker-compose --profile init run --rm init-db

REM ─── Iniciar servicios ─────────────────────────────────────────
echo ▶️  Iniciando servicios...
docker-compose up -d

REM ─── Verificar servicios ───────────────────────────────────────
echo 🔍 Verificando servicios...
timeout /t 10 /nobreak >nul

docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo.
    echo ❌ Error: Los servicios no se iniciaron correctamente
    echo Ejecuta: docker-compose logs
    pause
    exit /b 1
) else (
    echo.
    echo 🎉 ¡Factura CR está ejecutándose!
    echo.
    echo 📱 Dashboard: http://localhost:3000
    echo 🔗 API Docs: http://localhost:8000/docs
    echo 👤 Usuario de prueba: admin@test.cr / password
    echo.
    echo 📋 Comandos útiles:
    echo   docker-compose logs -f          # Ver logs en tiempo real
    echo   docker-compose ps               # Ver estado de servicios
    echo   docker-compose restart backend  # Reiniciar backend
    echo   docker-compose down             # Detener todo
    echo.
    echo 🚀 ¡Todo listo!
)

pause