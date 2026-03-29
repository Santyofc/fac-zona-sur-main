class DomainError(Exception):
    pass


class InvalidTransitionError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class IdempotencyConflictError(DomainError):
    pass
