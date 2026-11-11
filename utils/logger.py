"""
utils/logger.py — Centralised logging configuration for NetScope.

Call ``get_logger(__name__)`` in every module to obtain a named logger
that writes to both the console and a rotating log file in logs/.
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Import config lazily to avoid circular import issues during early startup.
# ---------------------------------------------------------------------------
_configured: bool = False


def _ensure_log_dir(log_dir: Path) -> None:
    """Create the logs directory if it does not exist."""
    log_dir.mkdir(parents=True, exist_ok=True)


def configure_logging(
    log_level: str = "INFO",
    log_file: Path | None = None,
    max_bytes: int = 5 * 1024 * 1024,
    backup_count: int = 3,
) -> None:
    """
    Configure the root logger once for the entire application.

    Parameters
    ----------
    log_level:
        A standard Python log-level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    log_file:
        Path to the rotating log file.  When *None* only a console handler is added.
    max_bytes:
        Maximum size in bytes before the log file is rotated.
    backup_count:
        Number of rotated backup files to keep.
    """
    global _configured
    if _configured:
        return  # Idempotent — only configure once per process.

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ── Console handler ──────────────────────────────────────────────────────
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # ── Rotating file handler ────────────────────────────────────────────────
    if log_file is not None:
        try:
            _ensure_log_dir(log_file.parent)
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except (OSError, PermissionError) as exc:
            # Log directory not writable (e.g. sandbox / test environment).
            # Fall back gracefully to console-only logging.
            root_logger.warning(
                "Could not create log file %s (%s). "
                "Falling back to console-only logging.",
                log_file,
                exc,
            )

    # Suppress noisy third-party loggers at WARNING level or above.
    for noisy in ("werkzeug", "urllib3", "scapy.runtime"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """
    Return a named logger.

    If logging has not been configured yet this function will apply default
    settings using values from config.py so that importing a module never
    silently drops log messages.
    """
    if not _configured:
        # Lazy import avoids circular dependency at module-load time.
        from config import LOG_LEVEL, LOG_FILE  # noqa: PLC0415

        configure_logging(log_level=LOG_LEVEL, log_file=LOG_FILE)

    return logging.getLogger(name)
