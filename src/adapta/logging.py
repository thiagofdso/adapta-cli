from __future__ import annotations

import importlib
import logging
from pathlib import Path


CURRENT_LOG_LEVEL: str | None = None


def resolve_log_level(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = value.strip().upper()
    if normalized not in {"INFO", "DEBUG"}:
        raise ValueError("Nível de log inválido. Use info ou debug.")
    return normalized


def configure_logging(log_level: str | None, data_dir: Path | None = None) -> None:
    global CURRENT_LOG_LEVEL

    resolved = resolve_log_level(log_level)
    CURRENT_LOG_LEVEL = resolved
    logging.disable(logging.NOTSET)
    if resolved is None:
        logging.disable(logging.CRITICAL)
        _configure_backend_logging(None)
        return

    level = getattr(logging, resolved, logging.INFO)
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if data_dir:
        log_file = data_dir / "adapta.log"
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
        except OSError:
            # Fallback to stream only if directory is not writable
            pass

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
        force=True,
    )
    _configure_backend_logging(resolved)


def _configure_backend_logging(log_level: str | None) -> None:
    try:
        logger_module = importlib.import_module("utils.logger")
    except ModuleNotFoundError:
        return

    logger = getattr(logger_module, "logger", None)
    setup_logger = getattr(logger_module, "setup_logger", None)

    if log_level is None:
        if logger is not None and hasattr(logger, "remove"):
            logger.remove()
        return

    if callable(setup_logger):
        setup_logger(log_level)


def apply_current_backend_logging() -> None:
    _configure_backend_logging(CURRENT_LOG_LEVEL)
