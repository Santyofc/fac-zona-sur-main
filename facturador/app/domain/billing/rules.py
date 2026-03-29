import random
import string
from datetime import datetime

from app.domain.common.enums import DocumentStatus
from app.domain.common.exceptions import InvalidTransitionError


_ALLOWED = {
    DocumentStatus.DRAFT: {DocumentStatus.QUEUED, DocumentStatus.FAILED},
    DocumentStatus.QUEUED: {DocumentStatus.SIGNED, DocumentStatus.RETRYING, DocumentStatus.FAILED},
    DocumentStatus.SIGNED: {DocumentStatus.SUBMITTED, DocumentStatus.RETRYING, DocumentStatus.FAILED},
    DocumentStatus.SUBMITTED: {DocumentStatus.ACCEPTED, DocumentStatus.REJECTED, DocumentStatus.RETRYING, DocumentStatus.FAILED},
    DocumentStatus.RETRYING: {DocumentStatus.QUEUED, DocumentStatus.SIGNED, DocumentStatus.SUBMITTED, DocumentStatus.FAILED},
    DocumentStatus.ACCEPTED: set(),
    DocumentStatus.REJECTED: set(),
    DocumentStatus.FAILED: set(),
}


def validate_transition(current: DocumentStatus, target: DocumentStatus) -> None:
    if target not in _ALLOWED[current]:
        raise InvalidTransitionError(f'Invalid transition: {current.value} -> {target.value}')


def generate_consecutive(sequence_number: int, doc_type: str, branch: int = 1, terminal: int = 1) -> str:
    type_map = {'FE': '01', 'ND': '02', 'NC': '03', 'TE': '04'}
    type_code = type_map.get(doc_type, '01')
    return f'{branch:03d}{terminal:05d}{type_code}{sequence_number:010d}'


def generate_clave(cedula: str, consecutive: str, emission_date: datetime | None = None) -> str:
    dt = emission_date or datetime.utcnow()
    date_part = dt.strftime('%d%m%y')
    cedula_12 = ''.join(filter(str.isdigit, cedula)).zfill(12)[:12]
    security_code = ''.join(random.choices(string.digits, k=8))
    return f'506{date_part}{cedula_12}{consecutive}1{security_code}'
