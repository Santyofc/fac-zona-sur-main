"""
utils/clave_generator.py — Facade del generador de Clave Numérica de 50 dígitos

La clave es el identificador único de cada comprobante electrónico.
Estructura exacta (50 dígitos):
  [506][DDMMAA][CÉDULA 12d][CONSECUTIVO 20d][SITUACIÓN 1d][SEGURIDAD 8d]

Este módulo es una fachada limpia del engine central (clave.py)
para que el microservicio lo use directamente.
"""

from __future__ import annotations

import logging
import random
import string
from datetime import datetime
from typing import Optional

# Importar el engine central
from services.hacienda.clave import (
    generate_clave as _generate_clave,
    generate_consecutive as _generate_consecutive,
    validate_clave as _validate_clave,
    generate_security_code as _generate_security_code,
    DocType,
    Situation,
)

logger = logging.getLogger(__name__)

# Re-exportar enums para conveniencia
__all__ = [
    "generate_clave",
    "generate_consecutive",
    "validate_clave",
    "generate_security_code",
    "DocType",
    "Situation",
]


def generate_clave(
    cedula:          str,
    sequence_number: int,
    doc_type:        str     = "FE",
    cedula_type:     str     = "JURIDICA",
    emission_date:   Optional[datetime] = None,
    situation:       str     = "NORMAL",
    branch:          int     = 1,
    terminal:        int     = 1,
    security_code:   Optional[str] = None,
) -> tuple[str, str]:
    """
    Genera la Clave Numérica de 50 dígitos para un comprobante electrónico.

    Args:
        cedula:          Número de cédula del emisor (solo dígitos, se normaliza)
        sequence_number: Número de secuencia del comprobante (1–9,999,999,999)
        doc_type:        "FE", "ND", "NC", "TE"
        cedula_type:     "FISICA", "JURIDICA", "DIMEX", "NITE"
        emission_date:   Fecha de emisión (usa hora actual CR si None)
        situation:       "NORMAL", "CONTINGENCIA", "SIN_INTERNET"
        branch:          Número de sucursal (1–999)
        terminal:        Número de terminal (1–999)
        security_code:   Código de seguridad 8 dígitos (auto-generado si None)

    Returns:
        Tuple (clave_50_digitos: str, consecutivo_20_digitos: str)

    Example:
        >>> clave, consecutive = generate_clave("3101000000", 1, "FE")
        >>> print(len(clave))   # → 50
        >>> print(len(consecutive))   # → 20
    """
    doc_type_enum  = _doc_type_enum(doc_type)
    situation_enum = _situation_enum(situation)

    clave, consecutive = _generate_clave(
        cedula          = cedula,
        cedula_type     = cedula_type,
        sequence_number = sequence_number,
        doc_type        = doc_type_enum,
        emission_date   = emission_date,
        situation       = situation_enum,
        security_code   = security_code,
        branch          = branch,
        terminal        = terminal,
    )

    logger.info(
        f"[clave_generator] ✅ Clave generada\n"
        f"  Clave:       {clave}\n"
        f"  Consecutivo: {consecutive}"
    )
    return clave, consecutive


def generate_consecutive(
    sequence_number: int,
    doc_type:        str = "FE",
    branch:          int = 1,
    terminal:        int = 1,
) -> str:
    """
    Genera solo el número consecutivo de 20 dígitos.
    Si solo necesitas el consecutivo sin la clave completa.
    """
    return _generate_consecutive(
        sequence_number = sequence_number,
        doc_type        = _doc_type_enum(doc_type),
        branch          = branch,
        terminal        = terminal,
    )


def validate_clave(clave: str) -> dict:
    """
    Valida y descompone una clave de 50 dígitos en sus componentes.

    Returns:
        {pais, fecha, cedula, sucursal, terminal, tipo_doc, numero, situacion, cod_seguridad}

    Raises:
        ValueError: Si la clave no tiene exactamente 50 dígitos numéricos.
    """
    return _validate_clave(clave)


def generate_security_code() -> str:
    """Genera un código de seguridad aleatorio de 8 dígitos."""
    return _generate_security_code(8)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _doc_type_enum(doc_type: str) -> DocType:
    mapping = {
        "FE":   DocType.FACTURA_ELECTRONICA,
        "ND":   DocType.NOTA_DEBITO,
        "NC":   DocType.NOTA_CREDITO,
        "TE":   DocType.TIQUETE_ELECTRONICO,
        "CCE":  DocType.CONFIRMACION_COMPROBANTE,
        "CPCE": DocType.CONFIRMACION_PARCIAL,
    }
    if doc_type.upper() not in mapping:
        raise ValueError(f"Tipo de documento inválido: '{doc_type}'. Usar: FE, ND, NC, TE")
    return mapping[doc_type.upper()]


def _situation_enum(situation: str) -> Situation:
    mapping = {
        "NORMAL":       Situation.NORMAL,
        "CONTINGENCIA": Situation.CONTINGENCIA,
        "SIN_INTERNET": Situation.SIN_INTERNET,
    }
    return mapping.get(situation.upper(), Situation.NORMAL)
