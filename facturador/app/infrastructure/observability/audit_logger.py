import logging


class AuditLogger:
    def __init__(self):
        self.logger = logging.getLogger('audit')

    async def log(self, payload: dict):
        self.logger.info(payload)
