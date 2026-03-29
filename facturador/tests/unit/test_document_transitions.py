import pytest

from app.domain.billing.rules import validate_transition
from app.domain.common.enums import DocumentStatus
from app.domain.common.exceptions import InvalidTransitionError


def test_valid_transition_draft_to_queued():
    validate_transition(DocumentStatus.DRAFT, DocumentStatus.QUEUED)


def test_invalid_transition_draft_to_accepted():
    with pytest.raises(InvalidTransitionError):
        validate_transition(DocumentStatus.DRAFT, DocumentStatus.ACCEPTED)
