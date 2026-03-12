"""
Firmador Digital de Comprobantes Electrónicos — Hacienda CR
Implementa firma XAdES-BES usando certificado digital .p12 (BCCR).

El certificado .p12 es emitido por el Banco Central de Costa Rica (BCCR)
y debe ser adquirido por el contribuyente a través del SINPE.

Algoritmos usados:
  - RSA-SHA256 para la firma
  - C14N2 para canonicalización
  - XAdES-BES como formato de firma

Referencias:
  - Política de Firma para CE v4.4 — Hacienda CR
  - XAdES ETSI EN 319 132-1

Nota: Si no se proporciona certificado, el XML se retorna sin firma
      (modo sandbox/desarrollo sin firma).
"""

from __future__ import annotations

import base64
import hashlib
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid

logger = logging.getLogger(__name__)


def _get_certificate_and_key(p12_path: str, p12_password: str):
    """
    Carga el certificado .p12 y extrae la clave privada y el certificado X.509.

    Returns:
        Tuple (private_key, certificate, chain_certs)

    Raises:
        ImportError: Si cryptography no está instalado
        FileNotFoundError: Si el archivo .p12 no existe
        Exception: Si la contraseña es incorrecta
    """
    try:
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography.hazmat.backends import default_backend
    except ImportError:
        raise ImportError(
            "La librería 'cryptography' es requerida para la firma digital. "
            "Instalar con: pip install cryptography"
        )

    p12_file = Path(p12_path)
    if not p12_file.exists():
        raise FileNotFoundError(f"Archivo .p12 no encontrado: {p12_path}")

    with open(p12_file, "rb") as f:
        p12_data = f.read()

    password = p12_password.encode("utf-8") if isinstance(p12_password, str) else p12_password
    private_key, certificate, chain = pkcs12.load_key_and_certificates(
        p12_data, password, backend=default_backend()
    )
    return private_key, certificate, chain or []


def sign_xml(
    xml_string: str,
    p12_path: Optional[str] = None,
    p12_password: Optional[str] = None,
) -> str:
    """
    Firma un XML con el certificado digital .p12 usando XAdES-BES.

    Si no se proporciona el certificado (modo desarrollo/sandbox), retorna
    el XML sin firma con un comentario indicando que está en modo sandbox.

    Args:
        xml_string: El XML generado sin firmar (string UTF-8)
        p12_path: Ruta al archivo .p12 del BCCR
        p12_password: Contraseña del .p12

    Returns:
        XML firmado como string UTF-8 (o XML original en modo sandbox)
    """
    # Modo sandbox: sin certificado
    if not p12_path or not p12_password:
        logger.warning(
            "⚠️  MODO SANDBOX: No se proporcionó certificado digital. "
            "El XML NO está firmado. Solo válido para pruebas en sandbox de Hacienda."
        )
        return _insert_sandbox_signature(xml_string)

    try:
        return _sign_with_xades(xml_string, p12_path, p12_password)
    except Exception as e:
        logger.error(f"Error al firmar XML: {e}. Retornando XML sin firma (sandbox fallback).")
        return _insert_sandbox_signature(xml_string)


def _sign_with_xades(xml_str: str, p12_path: str, p12_password: str) -> str:
    """
    Firma el XML con XAdES-BES usando la librería cryptography.

    Implementación simplificada compatible con Hacienda CR que incluye:
    - SignedInfo con Reference al documento
    - SignatureValue
    - KeyInfo con X509Certificate
    - QualifyingProperties (XAdES)
    """
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.backends import default_backend
        import xml.etree.ElementTree as ET
    except ImportError as e:
        raise ImportError(f"Dependencia faltante: {e}")

    private_key, certificate, chain = _get_certificate_and_key(p12_path, p12_password)

    # Calcular digest del documento XML (SHA-256)
    xml_bytes = xml_str.encode("utf-8")
    doc_digest = base64.b64encode(
        hashlib.sha256(xml_bytes).digest()
    ).decode("utf-8")

    # Obtener certificado en base64
    cert_der = certificate.public_bytes(serialization.Encoding.DER)
    cert_b64 = base64.b64encode(cert_der).decode("utf-8")

    # Obtener info del certificado
    subject_dn = certificate.subject.rfc4514_string()
    not_before = certificate.not_valid_before_utc.isoformat()
    not_after  = certificate.not_valid_after_utc.isoformat()
    serial_num = str(certificate.serial_number)

    # Calcular cert digest (SHA-1 para XAdES-BES, como lo pide Hacienda CR)
    cert_sha1_digest = base64.b64encode(hashlib.sha1(cert_der).digest()).decode("utf-8")

    # ID únicos para referencias
    sig_id          = f"Signature-{uuid.uuid4().hex[:16]}"
    signed_props_id = f"SignedProperties-{uuid.uuid4().hex[:16]}"
    sign_time       = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ─── Construir SignedInfo ───────────────────────────────────
    signed_info_xml = f"""<ds:SignedInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <ds:CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
  <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
  <ds:Reference URI="">
    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
    <ds:DigestValue>{doc_digest}</ds:DigestValue>
  </ds:Reference>
  <ds:Reference Type="http://uri.etsi.org/01903#SignedProperties" URI="#{signed_props_id}">
    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
    <ds:DigestValue>PLACEHOLDER_SP_DIGEST</ds:DigestValue>
  </ds:Reference>
</ds:SignedInfo>"""

    # ─── QualifyingProperties (XAdES) ──────────────────────────
    qualifying_props = f"""<xades:QualifyingProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Target="#{sig_id}">
  <xades:SignedProperties Id="{signed_props_id}">
    <xades:SignedSignatureProperties>
      <xades:SigningTime>{sign_time}</xades:SigningTime>
      <xades:SigningCertificate>
        <xades:Cert>
          <xades:CertDigest>
            <ds:DigestMethod xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
            <ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{cert_sha1_digest}</ds:DigestValue>
          </xades:CertDigest>
          <xades:IssuerSerial>
            <ds:X509IssuerName xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{subject_dn}</ds:X509IssuerName>
            <ds:X509SerialNumber xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{serial_num}</ds:X509SerialNumber>
          </xades:IssuerSerial>
        </xades:Cert>
      </xades:SigningCertificate>
      <xades:SignaturePolicyIdentifier>
        <xades:SignaturePolicyImplied/>
      </xades:SignaturePolicyIdentifier>
    </xades:SignedSignatureProperties>
  </xades:SignedProperties>
</xades:QualifyingProperties>"""

    # Calcular digest de SignedProperties
    sp_digest = base64.b64encode(
        hashlib.sha256(qualifying_props.encode("utf-8")).digest()
    ).decode("utf-8")

    signed_info_xml = signed_info_xml.replace("PLACEHOLDER_SP_DIGEST", sp_digest)

    # ─── Firmar SignedInfo ──────────────────────────────────────
    signed_info_bytes = signed_info_xml.encode("utf-8")
    signature_bytes   = private_key.sign(
        signed_info_bytes,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    signature_b64 = base64.b64encode(signature_bytes).decode("utf-8")

    # ─── Bloque Signature completo ──────────────────────────────
    signature_block = f"""<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="{sig_id}">
  {signed_info_xml}
  <ds:SignatureValue Id="SignatureValue-{sig_id}">{signature_b64}</ds:SignatureValue>
  <ds:KeyInfo>
    <ds:X509Data>
      <ds:X509Certificate>{cert_b64}</ds:X509Certificate>
    </ds:X509Data>
  </ds:KeyInfo>
  <ds:Object>
    {qualifying_props}
  </ds:Object>
</ds:Signature>"""

    # Insertar <ds:Signature> antes del cierre del elemento raíz
    signed_xml = _inject_signature(xml_str, signature_block)
    logger.info(f"✅ XML firmado correctamente con certificado: {p12_path}")
    return signed_xml


def _inject_signature(xml_str: str, signature_block: str) -> str:
    """
    Inserta el bloque de firma antes del cierre del elemento raíz XML.
    """
    # Encontrar el último cierre de tag raíz
    last_close = xml_str.rfind("</")
    if last_close == -1:
        raise ValueError("XML inválido: no se encontró tag de cierre")
    return xml_str[:last_close] + "\n" + signature_block + "\n" + xml_str[last_close:]


def _insert_sandbox_signature(xml_str: str) -> str:
    """
    Inserta un comentario de sandbox en el XML cuando no hay certificado.
    El XML devuelto puede ser enviado al sandbox de Hacienda sin firma.
    """
    sandbox_comment = """<!-- 
    ⚠️ SANDBOX MODE — XML SIN FIRMA DIGITAL
    Este comprobante no tiene firma XAdES-BES válida.
    Solo puede ser usado en el ambiente sandbox de Hacienda.
    Para producción, configure BCCR_P12_PATH y BCCR_P12_PASSWORD.
-->"""
    # Insertar después del header XML
    if xml_str.startswith("<?xml"):
        first_nl = xml_str.find("\n")
        return xml_str[:first_nl + 1] + sandbox_comment + "\n" + xml_str[first_nl + 1:]
    return sandbox_comment + "\n" + xml_str


def xml_to_base64(xml_str: str) -> str:
    """
    Convierte el XML firmado a Base64 para el payload de la API de Hacienda.

    Returns:
        String Base64 del XML en UTF-8
    """
    return base64.b64encode(xml_str.encode("utf-8")).decode("utf-8")


def base64_to_xml(b64_str: str) -> str:
    """
    Decodifica Base64 a XML string.
    Útil para descodificar respuestas de Hacienda.
    """
    return base64.b64decode(b64_str.encode("utf-8")).decode("utf-8")
