"""
tests/test_network.py — Unit tests for scanner/network.py.

Tests cover:
  - netmask_to_prefix_length() — valid masks, edge cases, invalid input.
  - calculate_cidr() — host-to-network calculation, host bits stripped.
  - NetworkConfig.is_complete — completeness check logic.
  - get_network_config() — integration via mocked psutil and route.
  - get_all_network_configs() — multi-interface path.

System calls (psutil, subprocess) are mocked so tests run offline
without admin rights or a live network.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Make the project root importable regardless of how pytest is invoked.
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scanner.network import (
    NetworkConfig,
    calculate_cidr,
    get_all_network_configs,
    get_network_config,
    netmask_to_prefix_length,
)


# ===========================================================================
# netmask_to_prefix_length
# ===========================================================================


class TestNetmaskToPrefixLength:
    """Tests for :func:`netmask_to_prefix_length`."""

    @pytest.mark.parametrize(
        "mask, expected",
        [
            ("255.255.255.0", 24),
            ("255.255.0.0", 16),
            ("255.0.0.0", 8),
            ("255.255.255.128", 25),
            ("255.255.255.255", 32),
            ("0.0.0.0", 0),
        ],
    )
    def test_valid_masks(self, mask: str, expected: int) -> None:
        assert netmask_to_prefix_length(mask) == expected

    @pytest.mark.parametrize(
        "mask",
        [
            "not-a-mask",
            "999.0.0.0",
            "",
            "255.255.255",
            "abc",
        ],
    )
    def test_invalid_masks_return_none(self, mask: str) -> None:
        result = netmask_to_prefix_length(mask)
        assert result is None


# ===========================================================================
# calculate_cidr
# ===========================================================================


class TestCalculateCidr:
    """Tests for :func:`calculate_cidr`."""

    @pytest.mark.parametrize(
        "ip, mask, expected_cidr",
        [
            ("192.168.1.5", "255.255.255.0", "192.168.1.0/24"),
            ("10.0.0.42", "255.255.0.0", "10.0.0.0/16"),
            ("172.16.5.100", "255.255.255.0", "172.16.5.0/24"),
            ("192.168.0.1", "255.255.255.128", "192.168.0.0/25"),
            ("10.10.10.1", "255.0.0.0", "10.0.0.0/8"),
        ],
    )
    def test_calculates_network_address(
        self, ip: str, mask: str, expected_cidr: str
    ) -> None:
        """Host bits must be stripped; result is the network address."""
        assert calculate_cidr(ip, mask) == expected_cidr

    def test_returns_none_for_bad_ip(self) -> None:
        assert calculate_cidr("999.999.999.999", "255.255.255.0") is None

    def test_returns_none_for_bad_mask(self) -> None:
        assert calculate_cidr("192.168.1.1", "not-a-mask") is None

    def test_returns_none_for_empty_strings(self) -> None:
        assert calculate_cidr("", "") is None


# ===========================================================================
# NetworkConfig
# ===========================================================================


class TestNetworkConfig:
    """Tests for :class:`NetworkConfig` dataclass behaviour."""

    def test_is_complete_true_when_all_fields_set(self) -> None:
        cfg = NetworkConfig(
            interface_name="Ethernet",
            ip_address="192.168.1.5",
            subnet_mask="255.255.255.0",
            gateway="192.168.1.1",
            cidr="192.168.1.0/24",
            prefix_length=24,
        )
        assert cfg.is_complete is True

    def test_is_complete_false_when_gateway_missing(self) -> None:
        cfg = NetworkConfig(
            interface_name="Ethernet",
            ip_address="192.168.1.5",
            subnet_mask="255.255.255.0",
            gateway=None,
            cidr="192.168.1.0/24",
            prefix_length=24,
        )
        assert cfg.is_complete is False

    def test_is_complete_false_when_ip_missing(self) -> None:
        cfg = NetworkConfig(
            interface_name="Wi-Fi",
            ip_address=None,
            subnet_mask="255.255.255.0",
            gateway="192.168.1.1",
            cidr=None,
            prefix_length=None,
        )
        assert cfg.is_complete is False

    def test_str_representation(self) -> None:
        cfg = NetworkConfig(
            interface_name="Ethernet",
            ip_address="10.0.0.5",
            subnet_mask="255.255.0.0",
            gateway="10.0.0.1",
            cidr="10.0.0.0/16",
            prefix_length=16,
        )
        result = str(cfg)
        assert "Ethernet" in result
        assert "10.0.0.5" in result
        assert "10.0.0.0/16" in result


# ===========================================================================
# get_network_config — integration (mocked)
# ===========================================================================


def _make_mock_interface(
    name: str = "Ethernet",
    ip: str = "192.168.1.100",
    mask: str = "255.255.255.0",
) -> MagicMock:
    """Return a mock InterfaceInfo with the given parameters."""
    iface = MagicMock()
    iface.name = name
    iface.ipv4_address = ip
    iface.ipv4_netmask = mask
    iface.is_active = True
    return iface


class TestGetNetworkConfig:
    """Integration-style tests for :func:`get_network_config`, fully mocked."""

    @patch("scanner.network.get_default_gateway", return_value="192.168.1.1")
    @patch(
        "scanner.network.get_preferred_interface",
        return_value=_make_mock_interface(),
    )
    def test_returns_complete_config(self, _mock_iface, _mock_gw) -> None:
        config = get_network_config()
        assert config is not None
        assert config.ip_address == "192.168.1.100"
        assert config.subnet_mask == "255.255.255.0"
        assert config.gateway == "192.168.1.1"
        assert config.cidr == "192.168.1.0/24"
        assert config.prefix_length == 24
        assert config.is_complete

    @patch("scanner.network.get_preferred_interface", return_value=None)
    def test_returns_none_when_no_interface(self, _mock_iface) -> None:
        config = get_network_config()
        assert config is None

    @patch("scanner.network.get_default_gateway", return_value=None)
    @patch(
        "scanner.network.get_preferred_interface",
        return_value=_make_mock_interface(),
    )
    def test_config_incomplete_without_gateway(self, _mock_iface, _mock_gw) -> None:
        config = get_network_config()
        assert config is not None
        assert config.gateway is None
        assert config.is_complete is False

    @patch("scanner.network.get_default_gateway", return_value="10.0.0.1")
    @patch(
        "scanner.network.get_preferred_interface",
        return_value=_make_mock_interface(ip=None, mask=None),
    )
    def test_cidr_none_when_ip_missing(self, _mock_iface, _mock_gw) -> None:
        config = get_network_config()
        assert config is not None
        assert config.cidr is None
        assert config.ip_address is None


# ===========================================================================
# get_all_network_configs — multi-interface path
# ===========================================================================


class TestGetAllNetworkConfigs:
    """Tests for :func:`get_all_network_configs`."""

    @patch("scanner.network.get_default_gateway", return_value="192.168.1.1")
    @patch(
        "scanner.network.list_active_interfaces",
        return_value=[
            _make_mock_interface("Ethernet", "192.168.1.10", "255.255.255.0"),
            _make_mock_interface("Wi-Fi", "192.168.1.20", "255.255.255.0"),
        ],
    )
    def test_returns_one_config_per_interface(self, _mock_ifaces, _mock_gw) -> None:
        configs = get_all_network_configs()
        assert len(configs) == 2
        names = {c.interface_name for c in configs}
        assert "Ethernet" in names
        assert "Wi-Fi" in names

    @patch(
        "scanner.network.list_active_interfaces",
        return_value=[],
    )
    def test_empty_list_when_no_active_interfaces(self, _mock_ifaces) -> None:
        configs = get_all_network_configs()
        assert configs == []
