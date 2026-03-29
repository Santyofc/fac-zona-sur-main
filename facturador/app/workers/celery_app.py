from celery import Celery

from app.core.config import settings


celery_app = Celery('facturador', broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.task_default_queue = 'issue_document'
celery_app.conf.task_routes = {
    'app.workers.tasks.issue_document.issue_document_task': {'queue': 'issue_document'},
    'app.workers.tasks.check_document_status.check_document_status_task': {'queue': 'check_document_status'},
    'app.workers.tasks.send_document_email.send_document_email_task': {'queue': 'send_document_email'},
}
