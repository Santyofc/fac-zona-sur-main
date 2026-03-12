"""
Invoice Service — Lógica de negocio para facturas
Genera consecutivos y claves según el formato de Hacienda CR.
"""
import hashlib
from datetime import datetime


# ─── Formato Hacienda ─────────────────────────────────────────
# Clave: 50 dígitos
# Pos 1-3:   Código país (506)
# Pos 4-9:   Fecha (DDMMAA)
# Pos 10-21: Cédula emisor (12 dígitos, padded con ceros)
# Pos 22-40: Consecutivo del comprobante (20 dígitos)
#   - Pos 22-24: Sucursal (001)
#   - Pos 25-27: Terminal (001)
#   - Pos 28-29: Tipo comprobante (01=FE, 02=ND, 03=NC, 04=TE)
#   - Pos 30-40: Número de la factura (10 dígitos)
# Pos 41:    Situación (1=Normal, 2=Contingencia, 3=Sin Internet)
# Pos 42-50: Código de seguridad (8 dígitos aleatorios)

DOC_TYPE_CODES = {
    "FE": "01",
    "ND": "02",
    "NC": "03",
    "TE": "04",
    "CCE": "05",
    "CPCE": "06",
}


def generate_consecutive(consecutive_num: int, doc_type: str = "FE") -> str:
    """
    Genera el número consecutivo en formato Hacienda:
    SSS-TTT-TT-NNNNNNNNNN (20 dígitos sin guiones)
    sucursal(3) + terminal(3) + tipo(2) + número(10)
    """
    type_code = DOC_TYPE_CODES.get(doc_type, "01")
    return f"001001{type_code}{str(consecutive_num).zfill(10)}"


def generate_clave(
    province: str,
    consecutive: str,
    cedula: str,
    situation: str = "1",
    doc_type: str = "FE",
) -> str:
    """
    Genera la clave numérica de 50 dígitos requerida por Hacienda CR.

    Args:
        province: Código de provincia (1=SJ, 2=Alajuela, etc.)
        consecutive: Número consecutivo de 20 dígitos
        cedula: Cédula jurídica o física del emisor
        situation: 1=Normal, 2=Contingencia, 3=Sin Internet
        doc_type: Tipo de documento (FE, TE, NC, ND)

    Returns:
        Clave de 50 dígitos
    """
    now = datetime.utcnow()
    date_str = now.strftime("%d%m%y")  # DDMMAA (6 dígitos)

    # Cédula, solo números, paddeada a 12 dígitos
    cedula_clean = "".join(filter(str.isdigit, cedula)).zfill(12)[:12]

    # Código de seguridad: últimos 8 dígitos del hash SHA-256 del consecutivo
    security_hash = hashlib.sha256(consecutive.encode()).hexdigest()
    security_code = "".join(filter(str.isdigit, security_hash))[:8].zfill(8)

    clave = (
        f"{province}"          # 1 dígito
        f"{date_str}"          # 6 dígitos
        f"{cedula_clean}"      # 12 dígitos
        f"{consecutive}"       # 20 dígitos
        f"{situation}"         # 1 dígito
        f"{security_code}"     # 8 dígitos
    )
    # Hacienda requiere exactamente 50 dígitos
    assert len(clave) == 50, f"Clave inválida: {len(clave)} dígitos — {clave}"
    return clave
