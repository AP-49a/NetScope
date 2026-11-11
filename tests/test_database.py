"""
tests/test_database.py — Unit and integration tests for SQLite persistence.

Tests cover:
  - Database initialization and schema creation.
  - Device upsert: inserting new devices and updating existing devices.
  - Strict preservation of `first_seen` timestamp across updates.
  - State transitions: marking unseen devices as offline.
  - Scan session history recording and relational link creation.
  - Device and history retrieval with sorting and status filtering.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from database.db import get_db_connection, init_db
from database.models import (
    get_all_devices,
    get_scan_history,
    mark_unseen_devices_offline,
    record_scan_session,
    upsert_device,
)
from scanner.discovery import ScanResult


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Create a temporary SQLite database with initial schema."""
    db_file = tmp_path / "test_netscope.db"
    init_db(db_file)
    return db_file


# ===========================================================================
# 1. Database Initialization
# ===========================================================================


class TestDatabaseInit:
    """Tests for :func:`database.db.init_db`."""

    def test_init_creates_tables(self, temp_db: Path) -> None:
        with get_db_connection(temp_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row["name"] for row in cursor.fetchall()]

            assert "devices" in tables
            assert "scan_history" in tables
            assert "scan_results" in tables

    def test_init_is_idempotent(self, temp_db: Path) -> None:
        # Running init_db multiple times must not raise errors
        init_db(temp_db)
        init_db(temp_db)


# ===========================================================================
# 2. Device Upsert & Lifecycle Tests
# ===========================================================================


class TestDeviceUpsert:
    """Tests for :func:`database.models.upsert_device`."""

    def test_insert_new_device(self, temp_db: Path) -> None:
        dev_id = upsert_device(
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.50",
            hostname="host1.local",
            manufacturer="Intel",
            timestamp="2026-11-11T10:00:00Z",
            db_path=temp_db,
        )
        assert dev_id > 0

        devices = get_all_devices(db_path=temp_db)
        assert len(devices) == 1
        d = devices[0]
        assert d["mac_address"] == "00:11:22:33:44:55"
        assert d["ip_address"] == "192.168.1.50"
        assert d["hostname"] == "host1.local"
        assert d["manufacturer"] == "Intel"
        assert d["first_seen"] == "2026-11-11T10:00:00Z"
        assert d["last_seen"] == "2026-11-11T10:00:00Z"
        assert d["status"] == "online"

    def test_update_existing_device_preserves_first_seen(self, temp_db: Path) -> None:
        # First discovery at 10:00
        id1 = upsert_device(
            mac_address="AA:BB:CC:DD:EE:FF",
            ip_address="192.168.1.100",
            hostname="old-host",
            manufacturer="Apple",
            timestamp="2026-11-11T10:00:00Z",
            db_path=temp_db,
        )

        # Subsequent discovery at 11:30 with IP change
        id2 = upsert_device(
            mac_address="AA:BB:CC:DD:EE:FF",
            ip_address="192.168.1.105",
            hostname="new-host",
            manufacturer=None,  # Should retain Apple
            timestamp="2026-11-11T11:30:00Z",
            db_path=temp_db,
        )

        assert id1 == id2  # Same device record updated

        devices = get_all_devices(db_path=temp_db)
        assert len(devices) == 1
        d = devices[0]
        assert d["ip_address"] == "192.168.1.105"
        assert d["hostname"] == "new-host"
        assert d["manufacturer"] == "Apple"  # Preserved
        assert d["first_seen"] == "2026-11-11T10:00:00Z"  # Preserved!
        assert d["last_seen"] == "2026-11-11T11:30:00Z"  # Updated!


# ===========================================================================
# 3. Offline Transition Tests
# ===========================================================================


class TestDeviceOfflineTransitions:
    """Tests for :func:`database.models.mark_unseen_devices_offline`."""

    def test_unseen_devices_transition_to_offline(self, temp_db: Path) -> None:
        upsert_device("00:00:00:00:00:01", "192.168.1.1", db_path=temp_db)
        upsert_device("00:00:00:00:00:02", "192.168.1.2", db_path=temp_db)

        # Only device 1 answered in subsequent scan
        updated = mark_unseen_devices_offline(["00:00:00:00:00:01"], db_path=temp_db)
        assert updated == 1

        online = get_all_devices(status_filter="online", db_path=temp_db)
        offline = get_all_devices(status_filter="offline", db_path=temp_db)

        assert len(online) == 1
        assert online[0]["mac_address"] == "00:00:00:00:00:01"

        assert len(offline) == 1
        assert offline[0]["mac_address"] == "00:00:00:00:00:02"


# ===========================================================================
# 4. Scan Session History Tests
# ===========================================================================


class TestScanHistory:
    """Tests for :func:`database.models.record_scan_session`."""

    def test_record_scan_session(self, temp_db: Path) -> None:
        dev_id = upsert_device("11:22:33:44:55:66", "10.0.0.5", db_path=temp_db)

        result = ScanResult(
            cidr="10.0.0.0/24",
            interface_name="Ethernet",
            duration_seconds=1.45,
            started_at="2026-11-11T12:00:00Z",
            completed_at="2026-11-11T12:00:01Z",
            success=True,
        )

        scan_id = record_scan_session(result, device_ids=[dev_id], db_path=temp_db)
        assert scan_id > 0

        history = get_scan_history(limit=5, db_path=temp_db)
        assert len(history) == 1
        h = history[0]
        assert h["cidr"] == "10.0.0.0/24"
        assert h["interface_name"] == "Ethernet"
        assert h["duration_seconds"] == 1.45
        assert h["status"] == "completed"
