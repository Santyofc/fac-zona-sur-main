from enum import Enum


class DocumentType(str, Enum):
    INVOICE = 'FE'
    TICKET = 'TE'
    CREDIT_NOTE = 'NC'
    DEBIT_NOTE = 'ND'


class DocumentStatus(str, Enum):
    DRAFT = 'draft'
    QUEUED = 'queued'
    SIGNED = 'signed'
    SUBMITTED = 'submitted'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    RETRYING = 'retrying'
    FAILED = 'failed'


class HaciendaStatus(str, Enum):
    PROCESANDO = 'procesando'
    ACEPTADO = 'aceptado'
    RECHAZADO = 'rechazado'
    NO_ENCONTRADO = 'no_encontrado'
    ERROR = 'error'
