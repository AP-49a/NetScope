"""
tests/test_discovery.py — Comprehensive unit tests for network discovery.

Tests cover:
  - MAC OUI vendor lookups (known vendors, formatting tolerance, unknown vendors).
  - Hostname resolution (successful lookups, errors, timeouts, loopback shortcut).
  - Data models (DiscoveredDevice, ScanResult serialization).
  - Scapy ARP scan orchestration with mocked raw packet layers.
  - Exception and permission failure resilience.
"""

from __future__ import annotations

import socket
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from scapy.all import ARP

from scanner.discovery import DiscoveredDevice, ScanResult, scan_network
from scanner.hostname import resolve_hostname
from scanner.network import NetworkConfig
from scanner.oui import get_manufacturer, is_locally_administered, normalize_mac_prefix


# ===========================================================================
# 1. MAC OUI Vendor Lookup Tests
# ===========================================================================


class TestOuiLookup:
    """Tests for :mod:`scanner.oui`."""

    @pytest.mark.parametrize(
        "mac, expected_vendor",
        [
            ("00:17:F2:12:34:56", "Apple"),
            ("00-17-F2-12-34-56", "Apple"),
            ("0017f2123456", "Apple"),
            ("0017.f212.3456", "Apple"),
            ("00:07:AB:AA:BB:CC", "Samsung"),
            ("00:02:B3:11:22:33", "Intel"),
            ("b8:27:eb:aa:bb:cc", "Raspberry Pi Foundation"),
            ("00:00:0c:07:ac:01", "Cisco"),
            ("00:1d:0f:11:22:33", "TP-Link"),
            ("18:fe:34:aa:bb:cc", "Espressif"),
            ("00:15:5d:01:02:03", "Microsoft (Hyper-V)"),
            ("00:06:5b:12:34:56", "Dell"),
        ],
    )
    def test_known_vendors(self, mac: str, expected_vendor: str) -> None:
        assert get_manufacturer(mac) == expected_vendor

    @pytest.mark.parametrize(
        "mac",
        [
            "FF:FF:FF:FF:FF:FF",
            "02:00:00:00:00:00",
            "12:34:56:78:9A:BC",
            "",
            "invalid-mac",
            None,
        ],
    )
    def test_unrecognized_or_invalid_mac(self, mac: str | None) -> None:
        assert get_manufacturer(mac) is None

    def test_normalize_mac_prefix(self) -> None:
        assert normalize_mac_prefix("aa:bb:cc:dd:ee:ff") == "AABBCC"
        assert normalize_mac_prefix("AA-BB-CC-11-22-33") == "AABBCC"
        assert normalize_mac_prefix("123") is None
        assert normalize_mac_prefix("") is None

    @pytest.mark.parametrize(
        "mac, expected",
        [
            ("6A:A6:CB:CB:6D:B0", True),   # 2nd digit 'A' -> Locally administered
            ("32:36:EA:FD:1C:CE", True),   # 2nd digit '2' -> Locally administered
            ("E2:3E:4C:8E:14:91", True),   # 2nd digit '2' -> Locally administered
            ("7C:BF:77:CD:20:F8", False),  # 2nd digit 'C' -> Universally administered (Xiaomi)
            ("70:08:94:D2:A4:C5", False),  # 2nd digit '0' -> Universally administered
            ("00:17:F2:12:34:56", False),  # Apple
            ("", False),
            (None, False),
        ],
    )
    def test_is_locally_administered(self, mac: str | None, expected: bool) -> None:
        assert is_locally_administered(mac) is expected


# ===========================================================================
# 2. Hostname Resolution Tests
# ===========================================================================


class TestHostnameResolution:
    """Tests for :mod:`scanner.hostname`."""

    def test_loopback_shortcut(self) -> None:
        assert resolve_hostname("127.0.0.1") == "localhost"

    @patch("scanner.hostname.socket.gethostbyaddr")
    def test_successful_lookup(self, mock_gethost: MagicMock) -> None:
        mock_gethost.return_value = ("router.local", [], ["192.168.1.1"])
        assert resolve_hostname("192.168.1.1") == "router.local"

    @patch("scanner.hostname.socket.gethostbyaddr", side_effect=socket.herror(1, "Unknown host"))
    def test_unresolvable_ip(self, _mock: MagicMock) -> None:
        assert resolve_hostname("192.168.1.99") is None

    @patch("scanner.hostname.socket.gethostbyaddr", side_effect=socket.timeout)
    def test_timeout_handled(self, _mock: MagicMock) -> None:
        assert resolve_hostname("192.168.1.99", timeout=0.1) is None

    def test_invalid_input(self) -> None:
        assert resolve_hostname("") is None
        assert resolve_hostname(None) is None  # type: ignore[arg-type]


# ===========================================================================
# 3. Data Model Tests
# ===========================================================================


class TestDataModels:
    """Tests for :class:`DiscoveredDevice` and :class:`ScanResult`."""

    def test_discovered_device_serialization(self) -> None:
        dev = DiscoveredDevice(
            ip_address="192.168.1.10",
            mac_address="00:17:F2:12:34:56",
            hostname="my-macbook.local",
            manufacturer="Apple",
            status="online",
        )
        d = dev.to_dict()
        assert d["ip_address"] == "192.168.1.10"
        assert d["mac_address"] == "00:17:F2:12:34:56"
        assert d["hostname"] == "my-macbook.local"
        assert d["manufacturer"] == "Apple"
        assert d["status"] == "online"

    def test_scan_result_serialization(self) -> None:
        dev = DiscoveredDevice(ip_address="192.168.1.1", mac_address="00:00:0C:11:22:33")
        res = ScanResult(
            cidr="192.168.1.0/24",
            interface_name="Wi-Fi",
            devices=[dev],
            duration_seconds=1.250,
            started_at="2026-11-11T12:00:00Z",
            completed_at="2026-11-11T12:00:01Z",
            success=True,
        )
        assert res.device_count == 1
        d = res.to_dict()
        assert d["device_count"] == 1
        assert d["duration_seconds"] == 1.25
        assert d["success"] is True
        assert len(d["devices"]) == 1


# ===========================================================================
# 4. Scapy ARP Scanner Tests
# ===========================================================================


def _build_arp_response(ip: str, mac: str) -> tuple[MagicMock, MagicMock]:
    """Helper creating a simulated (sent, received) Scapy packet tuple."""
    sent = MagicMock()
    recv = MagicMock()
    recv_arp = MagicMock()
    recv_arp.psrc = ip
    recv_arp.hwsrc = mac

    def get_layer(cls: Any) -> Any:
        if cls == ARP:
            return recv_arp
        return MagicMock()

    recv.__getitem__.side_effect = get_layer
    return (sent, recv)


class TestScanNetwork:
    """Tests for :func:`scanner.discovery.scan_network`."""

    @patch("scanner.discovery.srp")
    @patch("scanner.discovery.resolve_hostname", return_value="nas.local")
    def test_successful_scan_with_devices(
        self,
        mock_hostname: MagicMock,
        mock_srp: MagicMock,
    ) -> None:
        mock_srp.return_value = (
            [
                _build_arp_response("192.168.1.1", "00:00:0C:11:22:33"),
                _build_arp_response("192.168.1.50", "B8:27:EB:AA:BB:CC"),
            ],
            [],  # unanswered
        )

        result = scan_network(
            cidr="192.168.1.0/24",
            interface_name="Ethernet",
            timeout=1.0,
            resolve_hostnames=True,
        )

        assert result.success is True
        assert result.device_count == 2
        assert result.duration_seconds > 0.0

        dev1 = result.devices[0]
        assert dev1.ip_address == "192.168.1.1"
        assert dev1.mac_address == "00:00:0C:11:22:33"
        assert dev1.manufacturer == "Cisco"
        assert dev1.hostname == "nas.local"

        dev2 = result.devices[1]
        assert dev2.ip_address == "192.168.1.50"
        assert dev2.manufacturer == "Raspberry Pi Foundation"

    @patch("scanner.discovery.srp")
    def test_empty_scan_results(self, mock_srp: MagicMock) -> None:
        mock_srp.return_value = ([], [])

        result = scan_network(
            cidr="192.168.1.0/24",
            interface_name="Wi-Fi",
            timeout=1.0,
        )

        assert result.success is True
        assert result.device_count == 0
        assert result.devices == []

    @patch("scanner.discovery.srp", side_effect=PermissionError("Npcap access denied"))
    def test_permission_error_handling(self, _mock_srp: MagicMock) -> None:
        result = scan_network(
            cidr="192.168.1.0/24",
            interface_name="Wi-Fi",
        )

        assert result.success is False
        assert "Permission denied" in (result.error_message or "")
        assert result.device_count == 0

    @patch("scanner.discovery.srp", side_effect=RuntimeError("Adapter reset"))
    def test_general_exception_handling(self, _mock_srp: MagicMock) -> None:
        result = scan_network(
            cidr="192.168.1.0/24",
            interface_name="Wi-Fi",
        )

        assert result.success is False
        assert "Adapter reset" in (result.error_message or "")

    @patch("scanner.discovery.get_network_config")
    @patch("scanner.discovery.srp", return_value=([], []))
    def test_auto_detect_network_params(
        self,
        mock_srp: MagicMock,
        mock_get_config: MagicMock,
    ) -> None:
        mock_get_config.return_value = NetworkConfig(
            interface_name="Ethernet 2",
            ip_address="10.0.0.15",
            subnet_mask="255.255.255.0",
            gateway="10.0.0.1",
            cidr="10.0.0.0/24",
            prefix_length=24,
        )

        result = scan_network()

        assert result.success is True
        assert result.cidr == "10.0.0.0/24"
        assert result.interface_name == "Ethernet 2"

    @patch("scanner.discovery.get_network_config", return_value=None)
    def test_missing_network_config_aborts_safely(
        self,
        _mock_get_config: MagicMock,
    ) -> None:
        result = scan_network()

        assert result.success is False
        assert "no active network interface" in (result.error_message or "")
