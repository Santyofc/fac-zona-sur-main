"""
Signer Service — Firma el XML de factura electrónica usando signxml/lxml.
Requiere el certificado .p12 de la Firma Digital BCCR (Banco Central de CR).

En modo sandbox, si no hay certificado configurado, retorna el XML sin firmar
con una advertencia de log.
"""
import logging
import base64
from lxml import etree

logger = logging.getLogger(__name__)


def sign_xml(xml_content: str, cert_path: str = None, cert_pin: str = None) -> str:
    """
    Firma el XML con el certificado digital del emisor.

    En sandbox/desarrollo sin certificado, retorna el XML tal cual
    (Hacienda sandbox acepta XML sin firma para pruebas).

    Args:
        xml_content: XML generado por xml_service.generate_invoice_xml
        cert_path: Ruta al archivo .p12 de la firma digital
        cert_pin: PIN del certificado

    Returns:
        XML firmado como string
    """
    if not cert_path or not cert_pin:
        logger.warning(
            "[Signer] No hay certificado configurado. "
            "Retornando XML sin firmar (solo válido en sandbox)."
        )
        return xml_content

    try:
        from signxml import XMLSigner, methods
        from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
        from cryptography.hazmat.backends import default_backend

        # Cargar el certificado P12
        with open(cert_path, "rb") as f:
            p12_data = f.read()

        private_key, certificate, additional_certs = load_key_and_certificates(
            p12_data, cert_pin.encode(), default_backend()
        )

        # Parsear el XML
        root = etree.fromstring(xml_content.encode("utf-8"))

        # Firmar
        signer = XMLSigner(
            method=methods.enveloped,
            digest_algorithm="sha256",
            signature_algorithm="rsa-sha256",
        )
        signed_root = signer.sign(
            root,
            key=private_key,
            cert=certificate,
            always_add_key_value=True,
        )

        return etree.tostring(
            signed_root, pretty_print=True, xml_declaration=True, encoding="UTF-8"
        ).decode("utf-8")

    except ImportError:
        logger.error("[Signer] signxml no está instalado. pip install signxml")
        return xml_content
    except Exception as e:
        logger.error(f"[Signer] Error firmando XML: {e}")
        raise RuntimeError(f"Error al firmar el XML: {e}") from e
