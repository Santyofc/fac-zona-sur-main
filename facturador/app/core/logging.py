import logging
import sys

import orjson


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
        }
        if hasattr(record, 'correlation_id'):
            payload['correlation_id'] = record.correlation_id
        if record.exc_info:
            payload['exc_info'] = self.formatException(record.exc_info)
        return orjson.dumps(payload).decode('utf-8')


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)
