"""Structured logging configuration.

Produces JSON-formatted log lines so logs can be ingested by
ELK Stack, Datadog, Azure Monitor, or any log aggregator.

Each log line includes:
- timestamp (ISO 8601)
- level
- logger name
- message
- request_id (when inside an API request)
- any extra fields passed by the caller

Usage:
    from backend.app.logging_config import setup_logging
    setup_logging()  # call once at startup
"""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        req_id = request_id_var.get("")
        if req_id:
            log_entry["request_id"] = req_id

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        for key in ("duration_ms", "status_code", "method", "path", "client_ip",
                     "agent", "tool", "category", "node"):
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = val

        return json.dumps(log_entry, default=str)


def setup_logging(level: str = "INFO") -> None:
    """Configure the root logger with JSON output to stdout."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    root.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").propagate = False
