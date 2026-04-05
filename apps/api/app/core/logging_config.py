import json
import logging
import sys
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JsonFormatter(logging.Formatter):
    _EXTRA_KEYS = frozenset(
        {"request_id", "method", "path", "status_code", "duration_ms"},
    )

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in self._EXTRA_KEYS:
            if key in record.__dict__ and record.__dict__[key] is not None:
                payload[key] = record.__dict__[key]
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def setup_logging(
    *,
    json_logs: bool = False,
    level: int = logging.INFO,
    log_file: Path | None = None,
    log_max_bytes: int = 10 * 1024 * 1024,
    log_backup_count: int = 5,
) -> None:
    root = logging.getLogger()
    root.setLevel(level)

    formatter: logging.Formatter
    if json_logs:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.handlers.clear()
    root.addHandler(stream)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=log_max_bytes,
            backupCount=log_backup_count,
            encoding="utf-8",
        )
        file_handler.setFormatter(JsonFormatter())
        root.addHandler(file_handler)

    # Structured access log lives on `app.http`; avoid duplicating uvicorn's line access log.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
