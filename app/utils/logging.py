import json
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Mapping


LOG_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
MAX_LOG_VALUE_LENGTH = 2000
MAX_LOG_ITEMS = 50
SENSITIVE_KEYS = {"authorization", "token", "access_token", "refresh_token", "cookie", "set-cookie"}


def configure_logging(level_name: str) -> None:
    log_level = getattr(logging, level_name.upper(), logging.INFO)
    logs_dir = _get_dated_logs_dir()
    logs_dir.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(LOG_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if not root_logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    _ensure_file_handler(root_logger, logs_dir / "app.log", log_level, formatter)

    system_logger = logging.getLogger("mini_program_api.system")
    system_logger.setLevel(log_level)
    system_logger.propagate = True
    _ensure_file_handler(system_logger, logs_dir / "system_requests.log", log_level, formatter)

    external_logger = logging.getLogger("mini_program_api.external")
    external_logger.setLevel(log_level)
    external_logger.propagate = True
    _ensure_file_handler(external_logger, logs_dir / "external_api.log", log_level, formatter)


def _ensure_file_handler(
    logger: logging.Logger,
    file_path: Path,
    log_level: int,
    formatter: logging.Formatter,
) -> None:
    resolved = str(file_path.resolve())
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler) and handler.baseFilename == resolved:
            handler.setLevel(log_level)
            handler.setFormatter(formatter)
            return

    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def serialize_log_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, bytes):
        return _truncate_text(value.decode("utf-8", errors="replace"))
    if isinstance(value, str):
        return _truncate_text(value)
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, Mapping):
        sanitized: dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= MAX_LOG_ITEMS:
                sanitized["..."] = f"truncated after {MAX_LOG_ITEMS} items"
                break
            key_text = str(key)
            if key_text.lower() in SENSITIVE_KEYS:
                sanitized[key_text] = "***"
                continue
            sanitized[key_text] = serialize_log_value(item)
        return sanitized
    if isinstance(value, list):
        items = [serialize_log_value(item) for item in value[:MAX_LOG_ITEMS]]
        if len(value) > MAX_LOG_ITEMS:
            items.append(f"truncated after {MAX_LOG_ITEMS} items")
        return items
    if isinstance(value, tuple):
        return serialize_log_value(list(value))
    return _truncate_text(str(value))


def parse_request_body(body: bytes, content_type: str | None) -> Any:
    if not body:
        return None
    content = body.decode("utf-8", errors="replace")
    if content_type and "application/json" in content_type.lower():
        try:
            return serialize_log_value(json.loads(content))
        except json.JSONDecodeError:
            return _truncate_text(content)
    return _truncate_text(content)


def build_system_request_log(
    *,
    request_id: str,
    method: str,
    path: str,
    query_params: Mapping[str, Any],
    client_ip: str | None,
    headers: Mapping[str, str],
    request_body: Any,
    status_code: int,
    elapsed_ms: float,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "method": method,
        "path": path,
        "query_params": serialize_log_value(dict(query_params)),
        "client_ip": client_ip,
        "headers": serialize_log_value(dict(headers)),
        "request_body": serialize_log_value(request_body),
        "status_code": status_code,
        "elapsed_ms": round(elapsed_ms, 2),
    }


def log_external_api_interaction(
    *,
    service_name: str,
    method: str,
    url: str,
    request_headers: Mapping[str, str],
    request_body: Any,
    status_code: int | None,
    response_body: Any = None,
    elapsed_ms: float | None = None,
    error: str | None = None,
) -> None:
    logger = logging.getLogger("mini_program_api.external")
    payload = {
        "service": service_name,
        "method": method,
        "url": url,
        "request_headers": serialize_log_value(dict(request_headers)),
        "request_body": serialize_log_value(request_body),
        "status_code": status_code,
        "response_body": serialize_log_value(response_body),
        "elapsed_ms": round(elapsed_ms, 2) if elapsed_ms is not None else None,
        "error": error,
    }
    logger.info("external_api=%s", json.dumps(payload, ensure_ascii=False))


def log_system_request(payload: dict[str, Any]) -> None:
    logger = logging.getLogger("mini_program_api.system")
    logger.info("system_request=%s", json.dumps(payload, ensure_ascii=False))


def start_timer() -> float:
    return time.perf_counter()


def elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


def _truncate_text(value: str) -> str:
    if len(value) <= MAX_LOG_VALUE_LENGTH:
        return value
    return f"{value[:MAX_LOG_VALUE_LENGTH]}...<truncated>"


def _get_dated_logs_dir() -> Path:
    date_folder = datetime.now().strftime("%Y%m%d")
    return Path("logs") / date_folder