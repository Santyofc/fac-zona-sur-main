class XAdESSigner:
    async def sign(self, xml_content: str, cert_path: str, cert_password: str) -> str:
        try:
            from signxml import XMLSigner, methods
            from lxml import etree
            from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
        except ImportError as exc:
            raise RuntimeError('XAdES dependencies not installed (signxml/lxml/cryptography)') from exc

        if not cert_path or not cert_password:
            raise ValueError('certificate path and password are required')

        with open(cert_path, 'rb') as file:
            p12_data = file.read()

        private_key, certificate, _ = load_key_and_certificates(p12_data, cert_password.encode('utf-8'))
        if not private_key or not certificate:
            raise ValueError('invalid p12 certificate')

        root = etree.fromstring(xml_content.encode('utf-8'))
        signer = XMLSigner(method=methods.enveloped, signature_algorithm='rsa-sha256', digest_algorithm='sha256')
        signed = signer.sign(root, key=private_key, cert=certificate)
        return etree.tostring(signed, xml_declaration=True, encoding='UTF-8').decode('utf-8')
