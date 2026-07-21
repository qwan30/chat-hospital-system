import datetime
import json
import logging
import sys

try:
    from datetime import UTC
except ImportError:
    from datetime import timezone

    UTC = timezone.utc  # noqa: UP017


class OTelJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        message = record.getMessage()
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "message": message,
            "timestamp": datetime.datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        try:
            from opentelemetry import trace

            current_span = trace.get_current_span()
            if current_span and current_span.get_span_context().is_valid:
                span_context = current_span.get_span_context()
                log_data["trace_id"] = trace.format_trace_id(span_context.trace_id)
                log_data["span_id"] = trace.format_span_id(span_context.span_id)
        except ImportError:
            pass

        return json.dumps(log_data)


def configure_logging(level: str = "INFO", log_format: str = "text") -> None:
    handler = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        handler.setFormatter(OTelJsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))

    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=[handler],
    )
