"""
Hacienda CR Microservice — Package Init
Expone la API pública del microservicio de forma limpia.

Uso rápido:
    from services.hacienda import (
        generate_clave,
        generate_xml,
        XadesSigner,
        xml_to_base64,
        AuthService,
        send_invoice,
        check_status,
        process_invoice,
    )
"""

# Core engine
from .clave         import generate_clave, generate_consecutive, validate_clave, DocType, Situation
from .xml_generator import generate_xml
from .signer        import sign_xml, xml_to_base64, base64_to_xml
from .api_client    import HaciendaClient, HaciendaAPIError
from .hacienda      import process_invoice

# Microservice modules
from .auth_service  import AuthService, AuthenticationError
from .send_invoice  import send_invoice as send_invoice_fn, InvoiceSendResult
from .check_status  import check_status as check_status_fn, StatusResult, ComprobanteStatus

# Sub-package facades
from .xml.factura_xml         import (
    build_factura_electronica,
    build_tiquete_electronico,
    build_nota_credito,
    build_nota_debito,
    get_totals,
)
from .signing.xades_signer    import XadesSigner, XadesSignerError
from .utils.base64_encoder    import xml_to_base64 as encode_b64, base64_to_xml as decode_b64
from .utils.clave_generator   import (
    generate_clave as gen_clave,
    generate_consecutive as gen_consecutive,
    validate_clave as val_clave,
)

__version__ = "4.4.0"
__all__ = [
    # Core
    "generate_clave", "generate_consecutive", "validate_clave",
    "DocType", "Situation",
    "generate_xml",
    "sign_xml", "xml_to_base64", "base64_to_xml",
    "HaciendaClient", "HaciendaAPIError",
    "process_invoice",
    # Microservice
    "AuthService", "AuthenticationError",
    "send_invoice_fn", "InvoiceSendResult",
    "check_status_fn", "StatusResult", "ComprobanteStatus",
    # XML facade
    "build_factura_electronica", "build_tiquete_electronico",
    "build_nota_credito", "build_nota_debito", "get_totals",
    # Signing
    "XadesSigner", "XadesSignerError",
    # Utils
    "encode_b64", "decode_b64",
    "gen_clave", "gen_consecutive", "val_clave",
]
