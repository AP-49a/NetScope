"""
tests/test_api.py — Integration tests for Flask application and REST API endpoints.

Tests verify:
  - Dashboard root route (GET /).
  - Network configuration endpoint (GET /api/network).
  - Scan execution endpoint (POST /api/scan) with validation and 409 conflict handling.
  - Scanner status polling (GET /api/status).
  - Discovered device collection (GET /api/devices).
  - ScanService state machine transitions and concurrency protection.
"""

from __future__ import annotations

from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from app import create_app
from scanner.discovery import DiscoveredDevice, ScanResult
from scanner.network import NetworkConfig
from services.scan_service import ScanService, ScanState, scan_service


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Provide a test client for the configured Flask application."""
    scan_service.reset_state_for_testing()
    test_app = create_app({"TESTING": True})
    with test_app.test_client() as test_client:
        yield test_client
    scan_service.reset_state_for_testing()


# ===========================================================================
# 1. Dashboard Root Route
# ===========================================================================


class TestDashboardRoute:
    """Tests for GET /."""

    def test_index_serves_html(self, client: FlaskClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert b"NetScope" in response.data


# ===========================================================================
# 2. Network Configuration Endpoint (GET /api/network)
# ===========================================================================


class TestNetworkEndpoint:
    """Tests for GET /api/network."""

    @patch("api.routes.get_network_config")
    def test_get_network_success(self, mock_get_cfg: MagicMock, client: FlaskClient) -> None:
        mock_get_cfg.return_value = NetworkConfig(
            interface_name="Wi-Fi",
            ip_address="192.168.1.25",
            subnet_mask="255.255.255.0",
            gateway="192.168.1.1",
            cidr="192.168.1.0/24",
            prefix_length=24,
        )

        response = client.get("/api/network")
        assert response.status_code == 200
        data = response.get_json()

        assert data["interface_name"] == "Wi-Fi"
        assert data["ip_address"] == "192.168.1.25"
        assert data["subnet_mask"] == "255.255.255.0"
        assert data["gateway"] == "192.168.1.1"
        assert data["cidr"] == "192.168.1.0/24"
        assert data["prefix_length"] == 24
        assert data["is_complete"] is True

    @patch("api.routes.get_network_config", return_value=None)
    def test_get_network_none(self, _mock: MagicMock, client: FlaskClient) -> None:
        response = client.get("/api/network")
        assert response.status_code == 200
        data = response.get_json()
        assert data["is_complete"] is False
        assert data["interface_name"] is None

    @patch("api.routes.get_network_config", side_effect=RuntimeError("Introspection failed"))
    def test_get_network_exception_returns_500(self, _mock: MagicMock, client: FlaskClient) -> None:
        response = client.get("/api/network")
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data


# ===========================================================================
# 3. Status and Device Retrieval Endpoints
# ===========================================================================


class TestStatusAndDevicesEndpoints:
    """Tests for GET /api/status and GET /api/devices."""

    def test_initial_status_is_idle(self, client: FlaskClient) -> None:
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "idle"
        assert data["is_scanning"] is False
        assert data["last_scan"] is None

    def test_initial_devices_empty(self, client: FlaskClient) -> None:
        response = client.get("/api/devices")
        assert response.status_code == 200
        data = response.get_json()
        assert "devices" in data

    def test_get_history_endpoint(self, client: FlaskClient) -> None:
        response = client.get("/api/history")
        assert response.status_code == 200
        data = response.get_json()
        assert "history" in data

    @patch("api.routes.set_device_custom_name")
    def test_patch_device_name_success(self, mock_set_name: MagicMock, client: FlaskClient) -> None:
        mock_set_name.return_value = True
        response = client.patch(
            "/api/devices/00:11:22:33:44:55",
            json={"custom_name": "Living Room TV"},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["custom_name"] == "Living Room TV"
        assert data["mac_address"] == "00:11:22:33:44:55"

    @patch("api.routes.set_device_custom_name", return_value=False)
    def test_patch_device_name_not_found(self, _mock: MagicMock, client: FlaskClient) -> None:
        response = client.patch(
            "/api/devices/FF:FF:FF:FF:FF:FF",
            json={"custom_name": "Nonexistent"},
        )
        assert response.status_code == 404


# ===========================================================================
# 4. Scan Initiation Endpoint (POST /api/scan)
# ===========================================================================


class TestScanEndpoint:
    """Tests for POST /api/scan."""

    @patch("api.routes.scan_service.start_scan")
    def test_start_scan_success(self, mock_start: MagicMock, client: FlaskClient) -> None:
        mock_start.return_value = (True, "Scan initiated successfully.")

        response = client.post("/api/scan", json={"timeout": 1.5, "cidr": "192.168.1.0/24"})
        assert response.status_code == 202
        data = response.get_json()
        assert data["status"] == "scanning"
        assert data["target_cidr"] == "192.168.1.0/24"

    @patch("api.routes.scan_service.start_scan")
    def test_start_scan_conflict_when_already_scanning(
        self,
        mock_start: MagicMock,
        client: FlaskClient,
    ) -> None:
        mock_start.return_value = (False, "A network scan is currently in progress.")

        response = client.post("/api/scan")
        assert response.status_code == 409
        data = response.get_json()
        assert data["status"] == "scanning"
        assert "in progress" in data["error"]

    def test_invalid_timeout_negative(self, client: FlaskClient) -> None:
        response = client.post("/api/scan", json={"timeout": -1})
        assert response.status_code == 400
        data = response.get_json()
        assert "greater than 0" in data["error"]

    def test_invalid_timeout_non_numeric(self, client: FlaskClient) -> None:
        response = client.post("/api/scan", json={"timeout": "fast"})
        assert response.status_code == 400
        data = response.get_json()
        assert "numeric" in data["error"]


# ===========================================================================
# 5. ScanService Lifecycle & State Machine
# ===========================================================================


class TestScanServiceLifecycle:
    """Unit tests for :class:`ScanService` business logic."""

    @patch("services.scan_service.scan_network")
    def test_worker_success_lifecycle(self, mock_scan: MagicMock, tmp_path: Path) -> None:
        db_file = tmp_path / "lifecycle_test.db"
        with patch("database.db.DATABASE_PATH", db_file):
            service = ScanService()
            device = DiscoveredDevice(ip_address="192.168.1.10", mac_address="00:11:22:33:44:55")
            mock_scan.return_value = ScanResult(
                cidr="192.168.1.0/24",
                interface_name="Ethernet",
                devices=[device],
                duration_seconds=0.75,
                started_at="2026-11-11T00:00:00Z",
                completed_at="2026-11-11T00:00:01Z",
                success=True,
            )

            # Acquire lock to simulate start_scan state
            service._lock.acquire()
            service._state = ScanState.SCANNING

            service._run_scan_worker(cidr="192.168.1.0/24", interface_name="Ethernet", timeout=1.0)

            assert service.is_scanning is False
            assert service._state == ScanState.COMPLETED
            assert len(service.get_devices()) == 1
            assert service.get_devices()[0]["ip_address"] == "192.168.1.10"

    @patch("services.scan_service.scan_network")
    def test_worker_failure_lifecycle(self, mock_scan: MagicMock) -> None:
        service = ScanService()
        mock_scan.return_value = ScanResult(
            cidr="192.168.1.0/24",
            interface_name="Ethernet",
            devices=[],
            duration_seconds=0.1,
            started_at="2026-11-11T00:00:00Z",
            completed_at="2026-11-11T00:00:00Z",
            success=False,
            error_message="Permission denied",
        )

        service._lock.acquire()
        service._state = ScanState.SCANNING

        service._run_scan_worker(cidr="192.168.1.0/24", interface_name="Ethernet", timeout=1.0)

        assert service.is_scanning is False
        assert service._state == ScanState.ERROR
        status = service.get_status()
        assert status["error_message"] == "Permission denied"
