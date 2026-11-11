"""
tests/test_interface.py — Unit tests for scanner/interface.py.

Tests cover:
  - _classify_interface() — all InterfaceKind variants.
  - InterfaceInfo.is_active — active/inactive logic.
  - list_interfaces() — with mocked psutil.
  - list_active_interfaces() — filtering logic.
  - get_preferred_interface() — priority selection.

psutil is mocked throughout; no live network calls are made.
"""

from __future__ import annotations

import sys
import socket
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import psutil

# ---------------------------------------------------------------------------
# Make the project root importable.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scanner.interface import (
    InterfaceInfo,
    InterfaceKind,
    _classify_interface,
    get_preferred_interface,
    list_active_interfaces,
    list_interfaces,
)


# ===========================================================================
# _classify_interface
# ===========================================================================


class TestClassifyInterface:
    """Tests for the internal ``_classify_interface`` helper."""

    def test_loopback_flag_takes_priority(self) -> None:
        assert _classify_interface("Ethernet", is_loopback=True) == InterfaceKind.LOOPBACK

    @pytest.mark.parametrize(
        "name",
        ["vEthernet (Default Switch)", "VMware Network Adapter", "Docker NAT", "WSL"],
    )
    def test_virtual_patterns_detected(self, name: str) -> None:
        result = _classify_interface(name, is_loopback=False)
        assert result == InterfaceKind.VIRTUAL

    @pytest.mark.parametrize(
        "name",
        ["Wi-Fi", "Wireless Network Connection", "WLAN0"],
    )
    def test_wifi_patterns_detected(self, name: str) -> None:
        result = _classify_interface(name, is_loopback=False)
        assert result == InterfaceKind.WIFI

    @pytest.mark.parametrize(
        "name",
        ["Ethernet", "Ethernet 2", "Local Area Connection", "eth0"],
    )
    def test_ethernet_patterns_detected(self, name: str) -> None:
        result = _classify_interface(name, is_loopback=False)
        assert result == InterfaceKind.ETHERNET

    def test_unknown_for_unrecognised_name(self) -> None:
        result = _classify_interface("BlueTooth Network Connection 2", is_loopback=False)
        assert result == InterfaceKind.UNKNOWN


# ===========================================================================
# InterfaceInfo.is_active
# ===========================================================================


class TestInterfaceInfoIsActive:
    """Tests for :attr:`InterfaceInfo.is_active`."""

    def test_active_when_up_and_has_ip(self) -> None:
        iface = InterfaceInfo(
            name="Ethernet",
            kind=InterfaceKind.ETHERNET,
            is_up=True,
            ipv4_address="192.168.1.5",
        )
        assert iface.is_active is True

    def test_inactive_when_down(self) -> None:
        iface = InterfaceInfo(
            name="Ethernet",
            kind=InterfaceKind.ETHERNET,
            is_up=False,
            ipv4_address="192.168.1.5",
        )
        assert iface.is_active is False

    def test_inactive_when_no_ip(self) -> None:
        iface = InterfaceInfo(
            name="Ethernet",
            kind=InterfaceKind.ETHERNET,
            is_up=True,
            ipv4_address=None,
        )
        assert iface.is_active is False

    def test_inactive_when_down_and_no_ip(self) -> None:
        iface = InterfaceInfo(
            name="Wi-Fi",
            kind=InterfaceKind.WIFI,
            is_up=False,
            ipv4_address=None,
        )
        assert iface.is_active is False


# ===========================================================================
# list_interfaces (mocked psutil)
# ===========================================================================


def _build_stat(isup: bool = True, flags: str = "") -> MagicMock:
    stat = MagicMock()
    stat.isup = isup
    stat.flags = flags
    return stat


def _build_addr(family: int, address: str, netmask: str = "") -> MagicMock:
    addr = MagicMock()
    addr.family = family
    addr.address = address
    addr.netmask = netmask or None
    return addr


class TestListInterfaces:
    """Tests for :func:`list_interfaces` with mocked psutil."""

    @patch("scanner.interface.psutil.net_if_addrs")
    @patch("scanner.interface.psutil.net_if_stats")
    def test_returns_all_interfaces(self, mock_stats, mock_addrs) -> None:
        mock_stats.return_value = {
            "Ethernet": _build_stat(isup=True),
            "Wi-Fi": _build_stat(isup=False),
        }
        mock_addrs.return_value = {
            "Ethernet": [_build_addr(socket.AF_INET, "192.168.1.5", "255.255.255.0")],
            "Wi-Fi": [],
        }

        result = list_interfaces()
        assert len(result) == 2
        names = {i.name for i in result}
        assert "Ethernet" in names
        assert "Wi-Fi" in names

    @patch("scanner.interface.psutil.net_if_addrs")
    @patch("scanner.interface.psutil.net_if_stats")
    def test_ipv4_address_extracted(self, mock_stats, mock_addrs) -> None:
        mock_stats.return_value = {"Ethernet": _build_stat(isup=True)}
        mock_addrs.return_value = {
            "Ethernet": [_build_addr(socket.AF_INET, "10.0.0.5", "255.0.0.0")]
        }

        result = list_interfaces()
        ethernet = next(i for i in result if i.name == "Ethernet")
        assert ethernet.ipv4_address == "10.0.0.5"
        assert ethernet.ipv4_netmask == "255.0.0.0"

    @patch("scanner.interface.psutil.net_if_addrs", return_value={})
    @patch("scanner.interface.psutil.net_if_stats", return_value={})
    def test_empty_when_no_interfaces(self, _stats, _addrs) -> None:
        result = list_interfaces()
        assert result == []

    @patch("scanner.interface.psutil.net_if_addrs")
    @patch("scanner.interface.psutil.net_if_stats")
    def test_loopback_classified_correctly(self, mock_stats, mock_addrs) -> None:
        mock_stats.return_value = {
            "Loopback Pseudo-Interface 1": _build_stat(isup=True, flags="loopback")
        }
        mock_addrs.return_value = {
            "Loopback Pseudo-Interface 1": [
                _build_addr(socket.AF_INET, "127.0.0.1", "255.0.0.0")
            ]
        }

        result = list_interfaces()
        assert len(result) == 1
        assert result[0].kind == InterfaceKind.LOOPBACK


# ===========================================================================
# list_active_interfaces
# ===========================================================================


class TestListActiveInterfaces:
    """Tests for :func:`list_active_interfaces`."""

    @patch(
        "scanner.interface.list_interfaces",
        return_value=[
            InterfaceInfo("Ethernet", InterfaceKind.ETHERNET, is_up=True, ipv4_address="192.168.1.1"),
            InterfaceInfo("Wi-Fi", InterfaceKind.WIFI, is_up=False, ipv4_address=None),
            InterfaceInfo("vEthernet", InterfaceKind.VIRTUAL, is_up=True, ipv4_address="172.20.0.1"),
        ],
    )
    def test_returns_only_active_interfaces(self, _mock_list) -> None:
        active = list_active_interfaces()
        assert len(active) == 2
        assert all(i.is_active for i in active)


# ===========================================================================
# get_preferred_interface
# ===========================================================================


_ETHERNET = InterfaceInfo("Ethernet", InterfaceKind.ETHERNET, is_up=True, ipv4_address="192.168.1.5")
_WIFI = InterfaceInfo("Wi-Fi", InterfaceKind.WIFI, is_up=True, ipv4_address="192.168.1.6")
_VIRTUAL = InterfaceInfo("vEthernet", InterfaceKind.VIRTUAL, is_up=True, ipv4_address="172.20.0.1")


class TestGetPreferredInterface:
    """Tests for :func:`get_preferred_interface`."""

    @patch("scanner.interface.list_active_interfaces", return_value=[_ETHERNET, _WIFI])
    def test_prefers_named_interface(self, _mock) -> None:
        result = get_preferred_interface("Wi-Fi")
        assert result is not None
        assert result.name == "Wi-Fi"

    @patch("scanner.interface.list_active_interfaces", return_value=[_ETHERNET, _WIFI])
    def test_falls_back_to_ethernet_without_preference(self, _mock) -> None:
        result = get_preferred_interface("")
        assert result is not None
        assert result.kind == InterfaceKind.ETHERNET

    @patch("scanner.interface.list_active_interfaces", return_value=[_WIFI])
    def test_falls_back_to_wifi_when_no_ethernet(self, _mock) -> None:
        result = get_preferred_interface("")
        assert result is not None
        assert result.kind == InterfaceKind.WIFI

    @patch("scanner.interface.list_active_interfaces", return_value=[])
    def test_returns_none_when_no_active_interfaces(self, _mock) -> None:
        result = get_preferred_interface("")
        assert result is None

    @patch("scanner.interface.list_active_interfaces", return_value=[_ETHERNET, _WIFI])
    def test_fallback_when_named_interface_not_found(self, _mock) -> None:
        """Nonexistent preferred name → auto-select Ethernet."""
        result = get_preferred_interface("DoesNotExist")
        assert result is not None
        assert result.kind == InterfaceKind.ETHERNET

    @patch("scanner.interface.list_active_interfaces", return_value=[_VIRTUAL])
    def test_returns_none_when_only_virtual_active(self, _mock) -> None:
        """Only a virtual interface active → no suitable interface."""
        result = get_preferred_interface("")
        assert result is None
