"""Structured (JSON) logging with request/job context.

Logs carry ids (request, job, project, provider) — never media content,
transcripts or prompts, because uploaded videos may contain personal data.
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "log_context", default=None
)

_RESERVED = set(logging.LogRecord("", 0, "", 0, "", (), None).__dict__) | {"message"}


def bind_context(**values: Any) -> contextvars.Token:
    current = dict(_context.get() or {})
    current.update({k: v for k, v in values.items() if v is not None})
    return _context.set(current)


def reset_context(token: contextvars.Token) -> None:
    _context.reset(token)


def current_context() -> dict[str, Any]:
    return dict(_context.get() or {})


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "msg": record.getMessage(),
        }
        payload.update(current_context())
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        extras = {
            k: v for k, v in record.__dict__.items() if k not in _RESERVED and not k.startswith("_")
        }
        extras.update(current_context())
        if extras:
            base += " " + " ".join(f"{k}={v}" for k, v in extras.items())
        return base


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    handler = logging.StreamHandler(sys.stdout)
    if json_logs:
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(level.upper())
    # Quiet chatty libraries; their own errors still propagate.
    for noisy in ("botocore", "boto3", "urllib3", "s3transfer", "multipart"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
