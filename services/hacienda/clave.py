"""
Generador de Clave Numérica de 50 dígitos — Hacienda CR
Versión 4.4 del estándar de Comprobantes Electrónicos.

Estructura de la clave (50 dígitos exactos):
╔═══════════╤══════════╤══════════════════╤══════════════════════╤═══════════╤════════════════╗
║ País(3)   │ Fecha(6) │ Cédula Emisor(12) │ Consecutivo (20)     │ Situac(1) │ CódSeg.(8)     ║
║ 506       │ DDMMAA   │ 000000000000      │ SSS-TTT-TT-NNNNNNNNNN│ 1/2/3     │ 00000000       ║
╚═══════════╧══════════╧══════════════════╧══════════════════════╧═══════════╧════════════════╝

Consecutivo (20 dígitos):
  SSS       = Sucursal (001)
  TTTTT     = Terminal / PV (00001)
  TT        = Tipo comprobante (01=FE, 02=ND, 03=NC, 04=TE, 05=CCE, 06=CPCE)
  NNNNNNNNNN = Número (10 dígitos)

Situación:
  1 = Normal
  2 = Contingencia
  3 = Sin Internet

Referencias:
  - Anexos y Estructuras v4.4 — Ministerio de Hacienda CR
  - https://www.hacienda.go.cr/docs/Anexosyestructuras.pdf
"""

import random
import string
from datetime import datetime
from enum import IntEnum
from typing import Optional, Tuple, Dict


class DocType(IntEnum):
    """Tipo de comprobante electrónico según Hacienda CR."""
    FACTURA_ELECTRONICA = 1
    NOTA_DEBITO = 2
    NOTA_CREDITO = 3
    TIQUETE_ELECTRONICO = 4
    CONFIRMACION_COMPROBANTE = 5
    CONFIRMACION_PARCIAL = 6
    CONFIRMACION_RECHAZO = 7
    FACTURA_ELECTRONICA_EXPORTACION = 8
    FACTURA_ELECTRONICA_COMPRA = 9


class Situation(IntEnum):
    """Situación del comprobante."""
    NORMAL = 1
    CONTINGENCIA = 2
    SIN_INTERNET = 3


# Mapeo de tipo comprobante a código de 2 dígitos
DOC_TYPE_CODE: Dict[DocType, str] = {
    DocType.FACTURA_ELECTRONICA: "01",
    DocType.NOTA_DEBITO: "02",
    DocType.NOTA_CREDITO: "03",
    DocType.TIQUETE_ELECTRONICO: "04",
    DocType.CONFIRMACION_COMPROBANTE: "05",
    DocType.CONFIRMACION_PARCIAL: "06",
    DocType.CONFIRMACION_RECHAZO: "07",
    DocType.FACTURA_ELECTRONICA_EXPORTACION: "08",
    DocType.FACTURA_ELECTRONICA_COMPRA: "09",
}


def generate_consecutive(
    sequence_number: int,
    doc_type: DocType = DocType.FACTURA_ELECTRONICA,
    branch: int = 1,
    terminal: int = 1,
) -> str:
    """
    Genera el número consecutivo de 20 dígitos.

    Args:
        sequence_number: Número de secuencia (1-9,999,999,999)
        doc_type: Tipo de comprobante electrónico
        branch: Número de sucursal (1-999)
        terminal: Número de terminal (1-99,999)

    Returns:
        String de 20 dígitos: SSS-TTTTT-TT-NNNNNNNNNN (sin guiones)
    """
    if not (1 <= sequence_number <= 9_999_999_999):
        raise ValueError(f"Número de secuencia inválido: {sequence_number}. Debe ser 1-9,999,999,999")
    if not (1 <= branch <= 999):
        raise ValueError(f"Número de sucursal inválido: {branch}. Debe ser 1-999")
    if not (1 <= terminal <= 99_999):
        raise ValueError(f"Número de terminal inválido: {terminal}. Debe ser 1-99,999")

    type_code = DOC_TYPE_CODE[doc_type]
    consecutive = (
        f"{branch:03d}"           # SSS — sucursal (3 dígitos)
        f"{terminal:05d}"         # TTTTT — terminal/punto de venta (5 dígitos)
        f"{type_code}"            # TT  — tipo (2 dígitos)
        f"{sequence_number:010d}" # NNNNNNNNNN — número (10 dígitos)
    )
    assert len(consecutive) == 20, f"Consecutivo debe tener 20 dígitos: {consecutive}"
    return consecutive


def generate_security_code(length: int = 8) -> str:
    """Genera el código de seguridad de 8 dígitos aleatorios."""
    return "".join(random.choices(string.digits, k=length))


def generate_clave(
    cedula: str,
    consecutive: Optional[str] = None,
    sequence_number: Optional[int] = None,
    doc_type: DocType = DocType.FACTURA_ELECTRONICA,
    emission_date: Optional[datetime] = None,
    situation: Situation = Situation.NORMAL,
    security_code: Optional[str] = None,
    country_code: str = "506",
    branch: int = 1,
    terminal: int = 1,
) -> Tuple[str, str]:
    """
    Genera la Clave Numérica de 50 dígitos requerida por Hacienda CR (v4.4).
    """
    # Validar y limpiar cédula (solo dígitos, máx. 12)
    cedula_digits = "".join(filter(str.isdigit, cedula))
    if not cedula_digits:
        raise ValueError(f"Cédula inválida: {cedula}")
    cedula_padded = str(cedula_digits.zfill(12))[:12]

    # Fecha de emisión
    em_date = emission_date or datetime.now()
    date_part = em_date.strftime("%d%m%y")  # DDMMAA (6 dígitos)

    # Consecutivo
    if consecutive is None:
        if sequence_number is None:
            raise ValueError("Debe proveer consecutive o sequence_number")
        consecutive = generate_consecutive(sequence_number, doc_type, branch, terminal)
    
    cons_str = str(consecutive)

    # Situación
    situation_code = str(int(situation))

    # Código de seguridad
    if security_code is None:
        security_code = generate_security_code()
    sec_code_padded = str(security_code.zfill(8))[:8]

    # Construir clave
    clave = (
        f"{country_code}"    # 3 dígitos
        f"{date_part}"       # 6 dígitos
        f"{cedula_padded}"   # 12 dígitos
        f"{cons_str}"        # 20 dígitos
        f"{situation_code}"  # 1 dígito
        f"{sec_code_padded}" # 8 dígitos
    )

    if len(clave) != 50:
        raise RuntimeError(f"Clave generada tiene {len(clave)} dígitos (esperado: 50).")

    return clave, cons_str


def validate_clave(clave: str) -> Dict[str, str]:
    """Valida y descompone una clave de 50 dígitos."""
    if not clave.isdigit() or len(clave) != 50:
        raise ValueError(f"Clave inválida: debe tener 50 dígitos. Recibido: '{clave}'")

    p = str(clave)
    cons = p[21:41]

    return {
        "pais":          p[0:3],
        "fecha":         p[3:9],
        "cedula":        p[9:21],
        "sucursal":      cons[0:3],
        "terminal":      cons[3:8],
        "tipo_doc":      cons[8:10],
        "numero":        cons[10:20],
        "situacion":     p[41:42],
        "cod_seguridad": p[42:50],
        "consecutivo":   cons,
    }
