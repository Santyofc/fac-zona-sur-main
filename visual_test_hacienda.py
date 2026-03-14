import os
import asyncio
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from services.hacienda.api_client import HaciendaClient
from services.hacienda.clave import generate_clave, DocType
from services.hacienda.xml_generator import generate_xml
from services.hacienda.signer import sign_xml

# Configuración de logging estética
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("VisualTest")

async def run_visual_test():
    load_dotenv()
    
    print("\n" + "="*60)
    print(" [ZONA SUR TECH - HACIENDA V4.4 VISUAL TESTER]")
    print("="*60 + "\n")

    # 1. Cargar Credenciales
    username = os.getenv("HACIENDA_USERNAME")
    password = os.getenv("HACIENDA_PASSWORD")
    env = os.getenv("HACIENDA_ENV", "production")
    
    logger.info(f"[*] Usando entorno: {env.upper()}")
    logger.info(f"[*] Usuario: {username}")

    # 2. Inicializar Cliente
    client = HaciendaClient(
        username=username,
        password=password,
        environment=env
    )

    # 3. Preparar Datos de Prueba (Factura Electronica de Exportacion FEE)
    logger.info("[*] Generando datos para Factura de Exportacion (08)...")
    
    emisor = {
        "nombre": "ZONA SUR TECH SOCIEDAD ANONIMA",
        "tipo_cedula": "JURIDICA",
        "cedula": "3101111111",
        "correo": "facturacion@zonasurtech.com",
        "ubicacion": {
            "provincia": "1", "canton": "01", "distrito": "01", "otras_senas": "San Jose Central"
        }
    }
    
    receptor = {
        "nombre": "CLIENTE INTERNACIONAL S.A.",
        "tipo_cedula": "EXTRANJERO",
        "cedula": "999999999",
        "correo": "admin@international.com"
    }

    # Generar Clave y Consecutivo
    clave, consecutivo = generate_clave(
        cedula=emisor["cedula"],
        doc_type=DocType.FACTURA_ELECTRONICA_EXPORTACION,
        sequence_number=1,
        branch=1,
        terminal=1
    )
    
    logger.info(f"[*] Clave Generada: {clave}")
    logger.info(f"[*] Consecutivo:   {consecutivo}")

    # 4. Generar XML
    payload = {
        "doc_type": "FEE",
        "clave": clave,
        "consecutivo": consecutivo,
        "fecha_emision": datetime.now(timezone.utc).isoformat(),
        "codigo_actividad": "722000",
        "emisor": emisor,
        "receptor": receptor,
        "condicion_venta": "01",
        "medio_pago": ["01"],
        "moneda": "USD",
        "tipo_cambio": 520.0,
        "items": [
            {
                "linea_numero": 1,
                "cabys_code": "8314100000000", # Servicios de consultoría
                "detalle": "Desarrollo de Software SaaS Custom",
                "cantidad": 1,
                "unidad_medida": "Sp",
                "precio_unitario": 1500.00,
                "impuesto_codigo": "01",
                "impuesto_tarifa_codigo": "01", # 0% IVA para exportación (exento por ley)
                "impuesto_tarifa": 0
            }
        ]
    }
    
    logger.info("[*] Construyendo XML v4.4...")
    xml_raw = generate_xml(payload)
    
    # 5. Firmar XML (Simulado o real si existe certificado)
    p12_path = os.getenv("FIRMA_DIGITAL_PATH", "certificado.p12")
    p12_pass = os.getenv("FIRMA_DIGITAL_PIN", "1234") # El PIN que pedí al usuario
    
    logger.info(f"[*] Firmando XML con certificado: {p12_path}...")
    xml_signed = sign_xml(xml_raw, p12_path, p12_pass)
    
    if "SANDBOX MODE" in xml_signed:
        logger.warning("[!] IMPORTANTE: El XML no tiene firma valida (Modo Sandbox Fallback)")
    else:
        logger.info("[+] XML firmado correctamente.")

    # 6. Enviar a Hacienda
    logger.info("[*] Enviando comprobante a los servidores de Hacienda...")
    try:
        # Nota: Usamos emisor/receptor cedula sin guiones
        result = await client.send_comprobante(
            clave=clave,
            fecha_emision=payload["fecha_emision"],
            emisor_tipo="02",
            emisor_cedula=emisor["cedula"],
            receptor_tipo="05",
            receptor_cedula=receptor["cedula"],
            tipo_comprobante="08", # FEE
            xml_b64=client.xml_to_base64(xml_signed)
        )
        
        print("\n" + "[SUCCESS]" + "-"*58)
        print(f" RESULTADO API: {result.get('message', 'Sin mensaje')}")
        print(f" HTTP STATUS:  {result.get('status_code')}")
        print(f" HACIENDA:     {result.get('hacienda_status')}")
        print("[SUCCESS]" + "-"*58 + "\n")
        
    except Exception as e:
        print("\n" + "[ERROR]" + "-"*58)
        logger.error(f"Fallo en el envio: {e}")
        print("[ERROR]" + "-"*58 + "\n")

if __name__ == "__main__":
    asyncio.run(run_visual_test())
