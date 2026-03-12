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
  TTT       = Terminal (001)
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


class DocType(IntEnum):
    """Tipo de comprobante electrónico según Hacienda CR."""
    FACTURA_ELECTRONICA = 1
    NOTA_DEBITO = 2
    NOTA_CREDITO = 3
    TIQUETE_ELECTRONICO = 4
    CONFIRMACION_COMPROBANTE = 5
    CONFIRMACION_PARCIAL = 6


class Situation(IntEnum):
    """Situación del comprobante."""
    NORMAL = 1
    CONTINGENCIA = 2
    SIN_INTERNET = 3


# Mapeo de tipo comprobante a código de 2 dígitos
DOC_TYPE_CODE: dict[DocType, str] = {
    DocType.FACTURA_ELECTRONICA: "01",
    DocType.NOTA_DEBITO: "02",
    DocType.NOTA_CREDITO: "03",
    DocType.TIQUETE_ELECTRONICO: "04",
    DocType.CONFIRMACION_COMPROBANTE: "05",
    DocType.CONFIRMACION_PARCIAL: "06",
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
        terminal: Número de terminal (1-999)

    Returns:
        String de 20 dígitos: SSS-TTT-TT-NNNNNNNNNN (sin guiones)

    Raises:
        ValueError: Si sequence_number está fuera de rango
    """
    if not (1 <= sequence_number <= 9_999_999_999):
        raise ValueError(f"Número de secuencia inválido: {sequence_number}. Debe ser 1-9,999,999,999")
    if not (1 <= branch <= 999):
        raise ValueError(f"Número de sucursal inválido: {branch}. Debe ser 1-999")
    if not (1 <= terminal <= 999):
        raise ValueError(f"Número de terminal inválido: {terminal}. Debe ser 1-999")

    type_code = DOC_TYPE_CODE[doc_type]
    consecutive = (
        f"{branch:03d}"           # SSS — sucursal (3 dígitos)
        f"{terminal:03d}"         # TTT — terminal (3 dígitos)
        f"{type_code}"            # TT  — tipo (2 dígitos)
        f"{sequence_number:010d}" # NNNNNNNNNN — número (10 dígitos)
    )
    assert len(consecutive) == 20, f"Consecutivo debe tener 20 dígitos: {consecutive}"
    return consecutive


def generate_security_code(length: int = 8) -> str:
    """
    Genera el código de seguridad de 8 dígitos aleatorios.
    Se usa el pool de solo dígitos (0-9) para garantizar compatibilidad.
    """
    return "".join(random.choices(string.digits, k=length))


def generate_clave(
    cedula: str,
    cedula_type: str = "JURIDICA",
    consecutive: str = None,
    sequence_number: int = None,
    doc_type: DocType = DocType.FACTURA_ELECTRONICA,
    emission_date: datetime = None,
    situation: Situation = Situation.NORMAL,
    security_code: str = None,
    country_code: str = "506",
    branch: int = 1,
    terminal: int = 1,
) -> tuple[str, str]:
    """
    Genera la Clave Numérica de 50 dígitos requerida por Hacienda CR (v4.4).

    Puede recibir el consecutivo ya generado, o generarlo internamente.

    Args:
        cedula: Número de cédula del emisor (solo dígitos)
        cedula_type: Tipo cédula: FISICA, JURIDICA, DIMEX, NITE
        consecutive: Número consecutivo ya generado (20 dígitos). Si None, se genera.
        sequence_number: Número de secuencia (requerido si consecutive=None)
        doc_type: Tipo de comprobante
        emission_date: Fecha de emisión (hoy si None)
        situation: Situación del comprobante
        security_code: Código de seguridad (8 dígitos, auto-generado si None)
        country_code: Código de país "506" para Costa Rica
        branch: Número de sucursal
        terminal: Número de terminal

    Returns:
        Tuple (clave_50_digitos, numero_consecutivo_20_digitos)

    Raises:
        ValueError: Si la cédula es inválida o los parámetros están fuera de rango
    """
    # Validar y limpiar cédula (solo dígitos, máx. 12)
    cedula_digits = "".join(filter(str.isdigit, cedula))
    if len(cedula_digits) == 0:
        raise ValueError(f"Cédula inválida: {cedula}")
    cedula_padded = cedula_digits.zfill(12)[:12]

    # Fecha de emisión
    if emission_date is None:
        emission_date = datetime.now()
    date_part = emission_date.strftime("%d%m%y")  # DDMMAA (6 dígitos)

    # Consecutivo
    if consecutive is None:
        if sequence_number is None:
            raise ValueError("Debe proveer consecutive o sequence_number")
        consecutive = generate_consecutive(sequence_number, doc_type, branch, terminal)

    # Situación
    situation_code = str(int(situation))

    # Código de seguridad
    if security_code is None:
        security_code = generate_security_code()
    security_code = security_code.zfill(8)[:8]

    # Construir clave
    clave = (
        f"{country_code}"    # 3 dígitos — país
        f"{date_part}"       # 6 dígitos — fecha DDMMAA
        f"{cedula_padded}"   # 12 dígitos — cédula emisor
        f"{consecutive}"     # 20 dígitos — consecutivo
        f"{situation_code}"  # 1 dígito   — situación
        f"{security_code}"   # 8 dígitos  — código seguridad
    )

    # Validación final
    if len(clave) != 50:
        raise RuntimeError(
            f"ERROR CRÍTICO: Clave generada tiene {len(clave)} dígitos (esperado: 50).\n"
            f"Componentes:\n"
            f"  País:       {country_code} ({len(country_code)}d)\n"
            f"  Fecha:      {date_part} ({len(date_part)}d)\n"
            f"  Cédula:     {cedula_padded} ({len(cedula_padded)}d)\n"
            f"  Consecutivo:{consecutive} ({len(consecutive)}d)\n"
            f"  Situación:  {situation_code} ({len(situation_code)}d)\n"
            f"  Seg.:       {security_code} ({len(security_code)}d)\n"
            f"  TOTAL:      {clave}"
        )

    return clave, consecutive


def validate_clave(clave: str) -> dict:
    """
    Valida y descompone una clave de 50 dígitos en sus componentes.

    Returns:
        Dict con los campos de la clave, o lanza ValueError si es inválida.
    """
    if not clave.isdigit() or len(clave) != 50:
        raise ValueError(f"Clave inválida: debe tener exactamente 50 dígitos numéricos. Recibido: '{clave}' ({len(clave)} chars)")

    return {
        "pais":          clave[0:3],
        "fecha":         clave[3:9],
        "cedula":        clave[9:21],
        "sucursal":      clave[21:24],
        "terminal":      clave[24:27],
        "tipo_doc":      clave[27:29],
        "numero":        clave[29:39],
        "situacion":     clave[39],
        "cod_seguridad": clave[40:50],
        "consecutivo":   clave[21:41],
    }
