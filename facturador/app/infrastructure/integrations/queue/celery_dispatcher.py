from app.workers.tasks.issue_document import issue_document_task
from app.workers.tasks.check_document_status import check_document_status_task
from app.workers.tasks.send_document_email import send_document_email_task


class CeleryJobDispatcher:
    async def dispatch_issue(self, payload: dict) -> None:
        issue_document_task.delay(payload)

    async def dispatch_check_status(self, payload: dict) -> None:
        check_document_status_task.delay(payload)

    async def dispatch_send_email(self, payload: dict) -> None:
        send_document_email_task.delay(payload)
