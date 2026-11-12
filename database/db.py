"""
database/db.py — SQLite connection management and schema lifecycle.

Configures SQLite connection pool with Write-Ahead Logging (WAL) and foreign
key constraints, providing idempotent schema migrations.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from config import DATABASE_PATH
from utils.logger import get_logger

logger = get_logger(__name__)


@contextmanager
def get_db_connection(db_path: Optional[Path | str] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager providing a configured SQLite database connection.

    Enforces foreign keys, enables Write-Ahead Logging (WAL) for concurrency,
    and configures Row factory for dict-like row attribute access.
    """
    path_val = db_path if db_path is not None else DATABASE_PATH
    is_memory = str(path_val) == ":memory:"

    if not is_memory:
        target_file = Path(path_val)
        target_file.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(target_file), timeout=15.0)
    else:
        conn = sqlite3.connect(":memory:", timeout=15.0)

    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")

    if not is_memory:
        try:
            conn.execute("PRAGMA journal_mode = WAL;")
        except sqlite3.OperationalError:
            pass  # Fallback if journal mode cannot be changed

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[Path | str] = None) -> None:
    """
    Initialize SQLite database schema and secondary indexes idempotently.
    """
    logger.info("Initializing database schema at %s", db_path or DATABASE_PATH)

    schema_sql = """
    -- Devices table: maintains unique hardware observed over time
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mac_address TEXT NOT NULL UNIQUE,
        ip_address TEXT NOT NULL,
        hostname TEXT,
        custom_name TEXT,
        manufacturer TEXT,
        first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'online'
    );

    CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
    CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);

    -- Scan history audit table
    CREATE TABLE IF NOT EXISTS scan_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cidr TEXT NOT NULL,
        interface_name TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        duration_seconds REAL NOT NULL,
        device_count INTEGER NOT NULL DEFAULT 0,
        status TEXT NOT NULL,
        error_message TEXT
    );

    CREATE INDEX IF NOT EXISTS idx_scan_history_started ON scan_history(started_at);

    -- Scan-to-device join records
    CREATE TABLE IF NOT EXISTS scan_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scan_id INTEGER NOT NULL,
        device_id INTEGER NOT NULL,
        FOREIGN KEY (scan_id) REFERENCES scan_history(id) ON DELETE CASCADE,
        FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
    );
    """

    with get_db_connection(db_path) as conn:
        conn.executescript(schema_sql)
        # Migration: ensure custom_name column exists for pre-existing tables
        try:
            conn.execute("ALTER TABLE devices ADD COLUMN custom_name TEXT;")
        except sqlite3.OperationalError:
            pass  # Column already exists

    logger.info("Database schema initialized successfully.")
