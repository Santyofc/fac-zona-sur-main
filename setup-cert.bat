@echo off
REM ═══════════════════════════════════════════════════════════════
REM Script para configurar certificado Hacienda CR
REM ═══════════════════════════════════════════════════════════════

echo Configurando certificado digital para Hacienda CR...
echo.

REM Crear directorio certs si no existe
if not exist "services\api\certs" (
    mkdir services\api\certs
    echo ✓ Directorio certs creado
) else (
    echo ✓ Directorio certs ya existe
)

echo.
echo 📋 INSTRUCCIONES:
echo 1. Descarga tu certificado .p12 desde Hacienda ATV
echo 2. Copia el archivo como: services\api\certs\firma.p12
echo 3. El PIN ya está configurado en .env (2212)
echo.
echo Ruta completa: %CD%\services\api\certs\firma.p12
echo.

pause