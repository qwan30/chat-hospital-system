import json
import logging
import sys
from typing import Any

try:
    from opentelemetry import trace
except ImportError:
    trace = None


class OTelJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if trace:
            span_context = trace.get_current_span().get_span_context()
            if span_context and span_context.is_valid:
                log_data["trace_id"] = f"{span_context.trace_id:032x}"
                log_data["span_id"] = f"{span_context.span_id:16x}"

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging(level: str = "INFO", log_format: str = "text") -> None:
    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if log_format.lower() == "json":
        formatter = OTelJsonFormatter()
    else:
        formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

