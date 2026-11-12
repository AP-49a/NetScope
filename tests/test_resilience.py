"""
tests/test_resilience.py — Fault tolerance, input validation, and stress tests.

Tests verify:
  - Input validation: rejection of malformed CIDRs and payload types.
  - Failure recovery: hardware disconnects and driver failures do not permanently lock scanner.
  - Concurrency stress: rapid parallel scan requests enforce single-writer lock.
  - Subnet density stress: high-host volume simulation (250+ hosts) performance and safety.
"""

from __future__ import annotations

import concurrent.futures
import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from app import create_app
from database.db import init_db
from database.models import upsert_device
from scanner.discovery import DiscoveredDevice, ScanResult
from services.scan_service import scan_service


@pytest.fixture
def resilience_app(tmp_path: Path) -> Generator[FlaskClient, None, None]:
    """Test client with isolated temporary database."""
    db_file = tmp_path / "resilience_netscope.db"
    init_db(db_file)

    with patch("database.db.DATABASE_PATH", db_file):
        scan_service.reset_state_for_testing()
        app = create_app({"TESTING": True})
        with app.test_client() as client:
            yield client
        scan_service.reset_state_for_testing()


class TestInputValidation:
    """Tests for defensive parameter validation in API."""

    @pytest.mark.parametrize(
        "bad_cidr",
        [
            "999.999.999.0/24",
            "not-a-cidr",
            "192.168.1.1/99",
            "   ",
        ],
    )
    def test_invalid_cidr_returns_400(self, bad_cidr: str, resilience_app: FlaskClient) -> None:
        response = resilience_app.post("/api/scan", json={"cidr": bad_cidr})
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid CIDR" in data["error"] or "non-empty" in data["error"]


class TestFailureRecovery:
    """Tests verifying recovery after simulated hardware / driver exceptions."""

    @patch("services.scan_service.scan_network")
    def test_adapter_disconnect_recovery(self, mock_scan: MagicMock, resilience_app: FlaskClient) -> None:
        client = resilience_app

        # 1. Simulate adapter disconnection throwing OSError
        mock_scan.side_effect = OSError("Network is unreachable")

        res = client.post("/api/scan")
        assert res.status_code == 202

        if scan_service._active_thread:
            scan_service._active_thread.join(timeout=3.0)

        # Status should report error, but lock must be released
        status = client.get("/api/status").get_json()
        assert status["status"] == "error"
        assert scan_service.is_scanning is False

        # 2. Subsequent scan after network returns succeeds normally
        mock_scan.side_effect = None
        mock_scan.return_value = ScanResult(
            cidr="192.168.1.0/24",
            interface_name="Wi-Fi",
            devices=[],
            duration_seconds=0.5,
            started_at="2026-11-11T12:00:00Z",
            completed_at="2026-11-11T12:00:00Z",
            success=True,
        )

        res2 = client.post("/api/scan")
        assert res2.status_code == 202

        if scan_service._active_thread:
            scan_service._active_thread.join(timeout=3.0)

        status2 = client.get("/api/status").get_json()
        assert status2["status"] == "completed"


class TestConcurrencyStress:
    """Tests verifying lock integrity under parallel request bursts."""

    @patch("services.scan_service.scan_network")
    def test_concurrent_scan_lock_protection(self, mock_scan: MagicMock, resilience_app: FlaskClient) -> None:
        client = resilience_app

        # Simulate slow scan
        def slow_scan(*_args, **_kwargs):
            time.sleep(0.3)
            return ScanResult(
                cidr="10.0.0.0/24",
                interface_name="Ethernet",
                devices=[],
                duration_seconds=0.3,
                started_at="2026-11-11T12:00:00Z",
                completed_at="2026-11-11T12:00:00Z",
                success=True,
            )

        mock_scan.side_effect = slow_scan

        # Submit 10 concurrent requests
        app = resilience_app.application

        def make_request():
            with app.test_client() as thread_client:
                return thread_client.post("/api/scan").status_code

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]

        # Exactly 1 request should receive 202, while the other 9 receive 409
        assert results.count(202) == 1
        assert results.count(409) == 9

        if scan_service._active_thread:
            scan_service._active_thread.join(timeout=3.0)


class TestSubnetDensityStress:
    """Tests verifying performance under high host volume."""

    def test_high_density_host_processing(self, tmp_path: Path) -> None:
        db_file = tmp_path / "density_test.db"
        init_db(db_file)

        # Generate 254 simulated host records
        start = time.perf_counter()
        for i in range(1, 255):
            mac = f"00:50:56:{i:02X}:00:01"
            ip = f"192.168.1.{i}"
            upsert_device(mac_address=mac, ip_address=ip, manufacturer="VMware", db_path=db_file)

        duration = time.perf_counter() - start

        # Batch insertion of 254 records into SQLite should complete reasonably fast (< 10s on Windows)
        assert duration < 10.0
