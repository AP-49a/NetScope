"""
config.py — Centralised application configuration for NetScope.

All tuneable settings are read from environment variables (via .env).
Defaults are safe for local development on Windows 11.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Project root — always the directory that contains this file.
# ---------------------------------------------------------------------------
BASE_DIR: Path = Path(__file__).resolve().parent

# Load .env from the project root (silently ignored if absent).
load_dotenv(BASE_DIR / ".env", override=False)

# ---------------------------------------------------------------------------
# Flask
# ---------------------------------------------------------------------------
FLASK_HOST: str = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT: int = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() in ("1", "true", "yes")
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_DIR: Path = BASE_DIR / "logs"
LOG_FILE: Path = LOG_DIR / "netscope.log"

# Maximum log-file size before rotation (bytes) and backup count.
LOG_MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT: int = 3

# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------
# If set, the scanner will prefer this interface name; otherwise auto-detects.
PREFERRED_INTERFACE: str = os.getenv("PREFERRED_INTERFACE", "")
SCAN_TIMEOUT: float = float(os.getenv("SCAN_TIMEOUT", "2"))

# ---------------------------------------------------------------------------
# Database  (Phase 2 — declared here to avoid scattered magic strings later)
# ---------------------------------------------------------------------------
DATABASE_PATH: Path = BASE_DIR / os.getenv("DATABASE_PATH", "netscope.db")

# ---------------------------------------------------------------------------
# Static / template directories
# ---------------------------------------------------------------------------
TEMPLATES_DIR: Path = BASE_DIR / "templates"
STATIC_DIR: Path = BASE_DIR / "static"
