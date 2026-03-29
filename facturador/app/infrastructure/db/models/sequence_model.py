import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.base import Base


class SequenceModel(Base):
    __tablename__ = 'document_sequences'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'branch', 'terminal', 'doc_type', name='uq_sequence_scope'),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey('tenants.id', ondelete='CASCADE'), index=True)
    branch: Mapped[int] = mapped_column(Integer, default=1)
    terminal: Mapped[int] = mapped_column(Integer, default=1)
    doc_type: Mapped[str] = mapped_column(String(5))
    current_value: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
