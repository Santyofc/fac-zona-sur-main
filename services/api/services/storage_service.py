"""
Storage Service — Gestión de archivos en Supabase Storage o Neon
Maneja: PDFs, XMLs, certificados digitales
Soporta tanto Supabase como Neon para storage
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def upload_invoice_pdf(
    pdf_bytes: bytes,
    invoice_id: str,
    clave: str,
    company_id: str,
) -> Optional[str]:
    """
    Sube un PDF de factura a Supabase Storage (por ahora).
    En el futuro puede expandirse para usar Neon Storage.

    Args:
        pdf_bytes: Contenido del PDF en bytes
        invoice_id: ID de la factura
        clave: Número de comprobante (clave) de Hacienda
        company_id: ID de la empresa

    Returns:
        URL pública del PDF o None si falla
    """
    # Por ahora usamos Supabase, pero podemos agregar Neon Storage después
    return await _upload_to_supabase(pdf_bytes, invoice_id, clave, company_id, "pdf")


async def download_invoice_pdf(
    company_id: str,
    invoice_id: str,
    clave: str,
) -> Optional[bytes]:
    """
    Descarga un PDF de Supabase Storage.

    Args:
        company_id: ID de la empresa
        invoice_id: ID de la factura
        clave: Número de comprobante

    Returns:
        Contenido del PDF en bytes o None si falla
    """
    return await _download_from_supabase(company_id, invoice_id, clave, "pdf")


async def upload_invoice_xml(
    xml_bytes: bytes,
    invoice_id: str,
    clave: str,
    company_id: str,
) -> Optional[str]:
    """
    Sube XML firmado de factura a Supabase Storage.

    Args:
        xml_bytes: Contenido del XML en bytes
        invoice_id: ID de la factura
        clave: Número de comprobante
        company_id: ID de la empresa

    Returns:
        URL pública del XML o None si falla
    """
    return await _upload_to_supabase(xml_bytes, invoice_id, clave, company_id, "xml")


async def _upload_to_supabase(
    file_bytes: bytes,
    invoice_id: str,
    clave: str,
    company_id: str,
    file_type: str,
) -> Optional[str]:
    """Upload helper para Supabase"""
    try:
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL", "")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not supabase_url or not service_role_key:
            logger.error("❌ Supabase credentials not configured")
            return None

        supabase = create_client(supabase_url, service_role_key)

        # Path: invoices/{company_id}/{invoice_id}/{clave}.{file_type}
        bucket = "invoices"
        extension = "pdf" if file_type == "pdf" else "xml"
        filepath = f"{company_id}/{invoice_id}/{clave}.{extension}"

        # Upload
        logger.info(f"📤 Uploading {file_type.upper()}: {filepath}")
        response = supabase.storage.from_(bucket).upload(
            path=filepath,
            file=file_bytes,
            file_options={
                "cacheControl": "3600",
                "upsert": True,
                "contentType": f"application/{extension}"
            }
        )

        # Get public URL
        public_url = supabase.storage.from_(bucket).get_public_url(filepath)

        logger.info(f"✅ {file_type.upper()} uploaded: {public_url}")
        return public_url

    except Exception as e:
        logger.error(f"❌ Supabase upload failed: {e}")
        return None


async def _download_from_supabase(
    company_id: str,
    invoice_id: str,
    clave: str,
    file_type: str,
) -> Optional[bytes]:
    """Download helper para Supabase"""
    try:
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL", "")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not supabase_url or not service_role_key:
            logger.error("❌ Supabase credentials not configured")
            return None

        supabase = create_client(supabase_url, service_role_key)

        extension = "pdf" if file_type == "pdf" else "xml"
        filepath = f"{company_id}/{invoice_id}/{clave}.{extension}"
        bucket = "invoices"

        logger.info(f"📥 Downloading {file_type.upper()}: {filepath}")
        data = supabase.storage.from_(bucket).download(filepath)

        return data

    except Exception as e:
        logger.error(f"❌ Supabase download failed: {e}")
        return None


async def delete_invoice_files(
    company_id: str,
    invoice_id: str,
    clave: str,
) -> bool:
    """
    Elimina PDF y XML de una factura de Storage.

    Args:
        company_id: ID de la empresa
        invoice_id: ID de la factura
        clave: Número de comprobante

    Returns:
        True si se eliminaron, False si falla
    """
    try:
        from supabase import create_client

        supabase_url = os.getenv("SUPABASE_URL", "")
        service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not supabase_url or not service_role_key:
            return False

        supabase = create_client(supabase_url, service_role_key)
        bucket = "invoices"
        folder = f"{company_id}/{invoice_id}"

        # Listar archivos
        files = supabase.storage.from_(bucket).list(folder)

        # Eliminar cada archivo
        file_paths = [f"{folder}/{f['name']}" for f in files]
        if file_paths:
            supabase.storage.from_(bucket).remove(file_paths)
            logger.info(f"✅ Deleted {len(file_paths)} files from storage")

        return True

    except Exception as e:
        logger.error(f"❌ Storage deletion failed: {e}")
        return False
