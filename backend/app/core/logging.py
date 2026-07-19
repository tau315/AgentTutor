import logging
from contextvars import ContextVar


request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_context.get()
        return True

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
)

logger = logging.getLogger("agenttutor")
for handler in logging.getLogger().handlers:
    handler.addFilter(RequestIdFilter())
