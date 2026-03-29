from datetime import datetime

from sqlalchemy import select

from app.infrastructure.db.models.sequence_model import SequenceModel


class SQLAlchemySequenceRepository:
    def __init__(self, session):
        self.session = session

    async def next_sequence(self, tenant_id, branch, terminal, doc_type):
        result = await self.session.execute(
            select(SequenceModel)
            .where(
                SequenceModel.tenant_id == tenant_id,
                SequenceModel.branch == branch,
                SequenceModel.terminal == terminal,
                SequenceModel.doc_type == doc_type,
            )
            .with_for_update()
        )
        row = result.scalar_one_or_none()
        if not row:
            row = SequenceModel(
                tenant_id=tenant_id,
                branch=branch,
                terminal=terminal,
                doc_type=doc_type,
                current_value=0,
            )
            self.session.add(row)
            await self.session.flush()

        row.current_value += 1
        row.updated_at = datetime.utcnow()
        return row.current_value
