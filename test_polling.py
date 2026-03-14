"""
test_polling.py — Verificación del motor de consulta de estado (Production)
Este script prueba el flujo de:
1. Consultar estado en Hacienda usando una clave real
2. Actualizar la base de datos local usando el service 'refresh_invoice_status'
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Configurar path para importar servicios
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "services", "api")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from database import AsyncSessionLocal
from services.hacienda_service import refresh_invoice_status
from models.models import Invoice, HaciendaDocument

async def run_polling_test():
    from config import settings
    url = settings.ASYNC_DATABASE_URL
    # Obscure password for safety
    safe_url = url.replace(url.split(":")[2].split("@")[0], "****") if ":" in url and "@" in url else url
    
    print("\n" + "="*60)
    print(f"[*] INICIANDO TEST DE POLLING (HACIENDA PROD)")
    print(f"[*] Base de Datos: {safe_url}")
    print("="*60)

    # 1. Obtener la última factura de la base de datos que esté en estado 'processing'
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        # Buscamos la factura más reciente enviada a producción
        result = await db.execute(
            select(Invoice)
            .where(Invoice.clave != None)
            .order_by(Invoice.created_at.desc())
            .limit(1)
        )
        invoice = result.scalar_one_or_none()

        if not invoice:
            print("[ERROR] No se encontró ninguna factura con clave para probar.")
            return

        print(f"[*] Factura encontrada: ID={invoice.id} | Clave={invoice.clave[:20]}...")
        print(f"[*] Estado actual: {invoice.status}")

        # 2. Ejecutar el servicio de actualización
        print("\n[+] Ejecutando refresh_invoice_status...")
        try:
            result_data = await refresh_invoice_status(str(invoice.id), db)
            
            print("\n" + "-"*40)
            print(f"[SUCCESS] RESULTADO DE HACIENDA:")
            print(f"   - Estado: {result_data['hacienda_status']}")
            print(f"   - Mensaje: {result_data['hacienda_msg']}")
            print(f"   - Fecha Respuesta: {result_data['response_date']}")
            print("-"*40)
            
            # 3. Verificar persistencia
            print("\n[+] Verificando persistencia en DB...")
            await db.refresh(invoice)
            print(f"[*] Nuevo estado de la factura en DB: {invoice.status}")
            
            if invoice.status in ("sent", "rejected"):
                print("\n[SUCCESS] TEST COMPLETADO CON EXITO: Sincronizacion verificada.")
            else:
                print("\n[*] Factura en proceso o sin cambio. Reintente en unos momentos.")

        except Exception as e:
            print(f"\n[ERROR FATAL] {e}")

if __name__ == "__main__":
    # Cargar variables de entorno del API
    load_dotenv("services/api/.env")
    asyncio.run(run_polling_test())
