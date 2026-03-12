"""
signing/xades_signer.py — Firma Digital XAdES-BES para Hacienda CR

Responsabilidad: Cargar un certificado .p12 del BCCR y firmar el XML
del comprobante electrónico conforme a la política XAdES-BES definida por Hacienda.

La firma digital es obligatoria en producción. En sandbox, Hacienda acepta XML
sin firma válida, por lo que se incluye un modo de simulación de firma.

Estructura de firma XAdES-BES (simplificada, compatible con Hacienda):
  <ds:Signature>
    <ds:SignedInfo>
      <ds:CanonicalizationMethod>
      <ds:SignatureMethod>             RSA-SHA256
      <ds:Reference>                   Reference al documento
    </ds:SignedInfo>
    <ds:SignatureValue>               Firma en Base64
    <ds:KeyInfo>
      <ds:X509Data>
        <ds:X509Certificate>          Certificado B64
    <ds:Object>
      <xades:QualifyingProperties>   XAdES metadata
"""

from __future__ import annotations

import base64
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class XadesSignerError(Exception):
    """Error durante el proceso de firma XAdES."""
    pass


class XadesSigner:
    """
    Firmador XAdES-BES para comprobantes electrónicos de Hacienda CR.

    Uso:
        signer = XadesSigner(p12_path="/certs/bccr.p12", p12_password="secret")
        signed_xml = signer.sign(xml_str)
    """

    def __init__(
        self,
        p12_path:     Optional[str] = None,
        p12_password: Optional[str] = None,
        sandbox_mode: bool          = True,
    ):
        """
        Args:
            p12_path:     Ruta al archivo .p12 emitido por BCCR
            p12_password: Contraseña del archivo .p12
            sandbox_mode: Si True y no hay .p12, inserta comentario sandbox en lugar de firmar
        """
        self.p12_path     = p12_path
        self.p12_password = p12_password
        self.sandbox_mode = sandbox_mode
        self._private_key  = None
        self._certificate  = None

        if p12_path and p12_password:
            self._load_certificate()

    def _load_certificate(self) -> None:
        """Carga el certificado .p12 y extrae private_key + certificate."""
        try:
            from cryptography.hazmat.primitives.serialization import pkcs12
            from cryptography.hazmat.backends import default_backend
        except ImportError:
            raise XadesSignerError(
                "Librería 'cryptography' requerida: pip install cryptography"
            )

        p12_file = Path(self.p12_path)
        if not p12_file.exists():
            raise XadesSignerError(f"Archivo .p12 no encontrado: {self.p12_path}")

        with open(p12_file, "rb") as f:
            p12_data = f.read()

        password = (
            self.p12_password.encode("utf-8")
            if isinstance(self.p12_password, str)
            else self.p12_password
        )

        try:
            self._private_key, self._certificate, _ = pkcs12.load_key_and_certificates(
                p12_data, password, backend=default_backend()
            )
        except Exception as exc:
            raise XadesSignerError(
                f"No se pudo cargar el .p12. Contraseña incorrecta o archivo inválido: {exc}"
            ) from exc

        logger.info(f"[XadesSigner] ✅ Certificado cargado: {self.p12_path}")

    @property
    def has_certificate(self) -> bool:
        return self._private_key is not None and self._certificate is not None

    def sign(self, xml_str: str) -> str:
        """
        Firma el XML con XAdES-BES.

        Si no hay certificado y sandbox_mode=True, inserta un comentario
        de sandbox (válido solo para el ambiente de pruebas de Hacienda).

        Args:
            xml_str: XML del comprobante electrónico (sin firmar)

        Returns:
            XML con bloque <ds:Signature> insertado antes del cierre del root.

        Raises:
            XadesSignerError: Si hay error en el proceso de firma.
        """
        if not self.has_certificate:
            if self.sandbox_mode:
                logger.warning(
                    "[XadesSigner] ⚠️  Sin certificado .p12. Modo sandbox — XML sin firma real."
                )
                return self._sandbox_sign(xml_str)
            raise XadesSignerError(
                "No se puede firmar: no hay certificado .p12 configurado. "
                "Proveer BCCR_P12_PATH y BCCR_P12_PASSWORD, o activar sandbox_mode=True."
            )

        return self._xades_sign(xml_str)

    def _xades_sign(self, xml_str: str) -> str:
        """
        Implementa la firma XAdES-BES real usando el certificado BCCR.
        """
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
        except ImportError:
            raise XadesSignerError("Librería 'cryptography' requerida.")

        xml_bytes  = xml_str.encode("utf-8")
        doc_digest = base64.b64encode(hashlib.sha256(xml_bytes).digest()).decode()

        cert_der   = self._certificate.public_bytes(serialization.Encoding.DER)
        cert_b64   = base64.b64encode(cert_der).decode()
        cert_sha1  = base64.b64encode(hashlib.sha1(cert_der).digest()).decode()

        sign_time   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sig_id      = f"Sig-{uuid.uuid4().hex[:16]}"
        sp_id       = f"SP-{uuid.uuid4().hex[:16]}"
        subject_dn  = self._certificate.subject.rfc4514_string()
        serial_num  = str(self._certificate.serial_number)

        # QualifyingProperties
        qp = f"""<xades:QualifyingProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Target="#{sig_id}">
  <xades:SignedProperties Id="{sp_id}">
    <xades:SignedSignatureProperties>
      <xades:SigningTime>{sign_time}</xades:SigningTime>
      <xades:SigningCertificate>
        <xades:Cert>
          <xades:CertDigest>
            <ds:DigestMethod xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Algorithm="http://www.w3.org/2000/09/xmldsig#sha1"/>
            <ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{cert_sha1}</ds:DigestValue>
          </xades:CertDigest>
          <xades:IssuerSerial>
            <ds:X509IssuerName xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{subject_dn}</ds:X509IssuerName>
            <ds:X509SerialNumber xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{serial_num}</ds:X509SerialNumber>
          </xades:IssuerSerial>
        </xades:Cert>
      </xades:SigningCertificate>
      <xades:SignaturePolicyIdentifier><xades:SignaturePolicyImplied/></xades:SignaturePolicyIdentifier>
    </xades:SignedSignatureProperties>
  </xades:SignedProperties>
</xades:QualifyingProperties>"""

        sp_digest = base64.b64encode(hashlib.sha256(qp.encode()).digest()).decode()

        signed_info = f"""<ds:SignedInfo xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
  <ds:CanonicalizationMethod Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315"/>
  <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"/>
  <ds:Reference URI="">
    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
    <ds:DigestValue>{doc_digest}</ds:DigestValue>
  </ds:Reference>
  <ds:Reference Type="http://uri.etsi.org/01903#SignedProperties" URI="#{sp_id}">
    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
    <ds:DigestValue>{sp_digest}</ds:DigestValue>
  </ds:Reference>
</ds:SignedInfo>"""

        sig_bytes = self._private_key.sign(
            signed_info.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        sig_b64 = base64.b64encode(sig_bytes).decode()

        signature_block = f"""<ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="{sig_id}">
  {signed_info}
  <ds:SignatureValue Id="SigVal-{sig_id}">{sig_b64}</ds:SignatureValue>
  <ds:KeyInfo>
    <ds:X509Data><ds:X509Certificate>{cert_b64}</ds:X509Certificate></ds:X509Data>
  </ds:KeyInfo>
  <ds:Object>{qp}</ds:Object>
</ds:Signature>"""

        signed_xml = _inject_signature(xml_str, signature_block)
        logger.info(f"[XadesSigner] ✅ XML firmado con certificado BCCR ({len(signed_xml)} bytes)")
        return signed_xml

    def _sandbox_sign(self, xml_str: str) -> str:
        """Inserta un comentario sandbox en lugar de firma real."""
        comment = (
            "\n<!-- SANDBOX_MODE: XML sin firma XAdES válida. "
            "Solo para pruebas en sandbox.comprobanteselectronicos.go.cr -->"
        )
        if "<?xml" in xml_str[:10]:
            first_nl = xml_str.index("\n")
            return xml_str[:first_nl + 1] + comment + xml_str[first_nl + 1:]
        return comment + "\n" + xml_str


def _inject_signature(xml_str: str, signature_block: str) -> str:
    """Inserta el bloque <ds:Signature> antes del cierre del elemento raíz."""
    last_close = xml_str.rfind("</")
    if last_close == -1:
        raise XadesSignerError("XML inválido: no se encontró tag de cierre del elemento raíz")
    return xml_str[:last_close] + "\n" + signature_block + "\n" + xml_str[last_close:]
