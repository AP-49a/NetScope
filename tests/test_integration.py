"""
tests/test_integration.py — End-to-end integration tests for NetScope.

Exercises complete lifecycle across API, service layer, scanning engine,
and SQLite persistence:
  - Multi-scan lifecycle transitions (online -> offline).
  - First-seen timestamp preservation and last-seen updates.
  - History tracking and audit trails.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from app import create_app
from database.db import init_db
from scanner.discovery import DiscoveredDevice, ScanResult
from services.scan_service import scan_service


@pytest.fixture
def integration_app(tmp_path: Path) -> Generator[FlaskClient, None, None]:
    """Provide a test client wired to an isolated temporary SQLite database."""
    db_file = tmp_path / "integration_netscope.db"
    init_db(db_file)

    # Patch DATABASE_PATH in db module to use the temp database
    with patch("database.db.DATABASE_PATH", db_file):
        scan_service.reset_state_for_testing()
        app = create_app({"TESTING": True})
        with app.test_client() as client:
            yield client
        scan_service.reset_state_for_testing()


class TestEndToEndPipeline:
    """End-to-end integration tests."""

    @patch("services.scan_service.scan_network")
    def test_multi_scan_lifecycle(self, mock_scan: MagicMock, integration_app: FlaskClient) -> None:
        client = integration_app

        # -------------------------------------------------------------------
        # Scan 1: Discovers Host A (Router) and Host B (Laptop)
        # -------------------------------------------------------------------
        dev_a = DiscoveredDevice(
            ip_address="192.168.1.1",
            mac_address="00:00:0C:07:AC:01",
            hostname="router.local",
            manufacturer="Cisco",
            status="online",
        )
        dev_b = DiscoveredDevice(
            ip_address="192.168.1.50",
            mac_address="00:17:F2:11:22:33",
            hostname="laptop.local",
            manufacturer="Apple",
            status="online",
        )

        mock_scan.return_value = ScanResult(
            cidr="192.168.1.0/24",
            interface_name="Wi-Fi",
            devices=[dev_a, dev_b],
            duration_seconds=1.2,
            started_at="2026-11-11T10:00:00Z",
            completed_at="2026-11-11T10:00:01Z",
            success=True,
        )

        # Trigger Scan 1
        res1 = client.post("/api/scan", json={"cidr": "192.168.1.0/24"})
        assert res1.status_code == 202

        # Wait briefly for daemon worker thread to finish
        if scan_service._active_thread:
            scan_service._active_thread.join(timeout=3.0)

        # Verify devices from GET /api/devices
        res_devices1 = client.get("/api/devices")
        assert res_devices1.status_code == 200
        devices1 = res_devices1.get_json()["devices"]
        assert len(devices1) == 2

        dev_map1 = {d["mac_address"]: d for d in devices1}
        assert dev_map1["00:00:0C:07:AC:01"]["status"] == "online"
        assert dev_map1["00:17:F2:11:22:33"]["status"] == "online"
        host_b_first_seen = dev_map1["00:17:F2:11:22:33"]["first_seen"]

        # -------------------------------------------------------------------
        # Scan 2: Host A went offline; Host B got a new IP; Host C appeared
        # -------------------------------------------------------------------
        dev_b_updated = DiscoveredDevice(
            ip_address="192.168.1.55",  # IP changed via DHCP
            mac_address="00:17:F2:11:22:33",
            hostname="laptop.local",
            manufacturer="Apple",
            status="online",
        )
        dev_c = DiscoveredDevice(
            ip_address="192.168.1.99",
            mac_address="B8:27:EB:99:88:77",
            hostname="raspberrypi.local",
            manufacturer="Raspberry Pi Foundation",
            status="online",
        )

        mock_scan.return_value = ScanResult(
            cidr="192.168.1.0/24",
            interface_name="Wi-Fi",
            devices=[dev_b_updated, dev_c],
            duration_seconds=0.9,
            started_at="2026-11-11T11:00:00Z",
            completed_at="2026-11-11T11:00:01Z",
            success=True,
        )

        # Trigger Scan 2
        res2 = client.post("/api/scan")
        assert res2.status_code == 202

        if scan_service._active_thread:
            scan_service._active_thread.join(timeout=3.0)

        # Verify device lifecycle state transitions
        res_devices2 = client.get("/api/devices")
        assert res_devices2.status_code == 200
        devices2 = res_devices2.get_json()["devices"]
        assert len(devices2) == 3  # All 3 total devices retained!

        dev_map2 = {d["mac_address"]: d for d in devices2}

        # 1. Host A was absent in Scan 2 -> transitioned to offline
        assert dev_map2["00:00:0C:07:AC:01"]["status"] == "offline"

        # 2. Host B updated its IP and last_seen while preserving first_seen
        assert dev_map2["00:17:F2:11:22:33"]["status"] == "online"
        assert dev_map2["00:17:F2:11:22:33"]["ip_address"] == "192.168.1.55"
        assert dev_map2["00:17:F2:11:22:33"]["first_seen"] == host_b_first_seen

        # 3. Host C was added as online
        assert dev_map2["B8:27:EB:99:88:77"]["status"] == "online"
        assert dev_map2["B8:27:EB:99:88:77"]["manufacturer"] == "Raspberry Pi Foundation"

        # -------------------------------------------------------------------
        # Verify Scan History Audit Trail
        # -------------------------------------------------------------------
        res_hist = client.get("/api/history")
        assert res_hist.status_code == 200
        history = res_hist.get_json()["history"]
        assert len(history) == 2
