"""
scanner/network.py — Local network configuration detection.

Responsibilities (Phase 1):
  - Retrieve the IPv4 address, subnet mask, and default gateway for the
    active network interface.
  - Calculate the network CIDR block from the IP + mask.
  - Handle multiple interfaces and missing information gracefully.
  - No network scanning or packet sending in this phase.

Dependencies: psutil, standard library (ipaddress, socket, subprocess).
"""

from __future__ import annotations

import ipaddress
import subprocess
import re
from dataclasses import dataclass
from typing import Optional

from utils.logger import get_logger
from scanner.interface import InterfaceInfo, get_preferred_interface, list_active_interfaces

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


@dataclass
class NetworkConfig:
    """
    Complete network configuration for a single interface.

    All string fields are ``None`` when the value could not be determined.
    """

    interface_name: str
    """Name of the network interface this config describes."""

    ip_address: Optional[str]
    """Host IPv4 address (e.g. ``'192.168.1.5'``)."""

    subnet_mask: Optional[str]
    """Subnet mask in dotted-decimal form (e.g. ``'255.255.255.0'``)."""

    gateway: Optional[str]
    """Default gateway IPv4 address (e.g. ``'192.168.1.1'``)."""

    cidr: Optional[str]
    """Network address in CIDR notation (e.g. ``'192.168.1.0/24'``)."""

    prefix_length: Optional[int]
    """Prefix length derived from *subnet_mask* (e.g. ``24``)."""

    @property
    def is_complete(self) -> bool:
        """True when all four fields are populated."""
        return all(
            v is not None
            for v in (self.ip_address, self.subnet_mask, self.gateway, self.cidr)
        )

    def __str__(self) -> str:
        return (
            f"NetworkConfig("
            f"iface={self.interface_name!r}, "
            f"ip={self.ip_address}, "
            f"mask={self.subnet_mask}, "
            f"gateway={self.gateway}, "
            f"cidr={self.cidr})"
        )


# ---------------------------------------------------------------------------
# CIDR / subnet helpers
# ---------------------------------------------------------------------------


def netmask_to_prefix_length(netmask: str) -> Optional[int]:
    """
    Convert a dotted-decimal subnet mask to a prefix length integer.

    Parameters
    ----------
    netmask:
        A dotted-decimal subnet mask such as ``'255.255.255.0'``.

    Returns
    -------
    int or None
        Prefix length (0–32), or *None* if *netmask* is not a valid mask.

    Examples
    --------
    >>> netmask_to_prefix_length('255.255.255.0')
    24
    >>> netmask_to_prefix_length('255.255.0.0')
    16
    """
    try:
        network = ipaddress.IPv4Network(f"0.0.0.0/{netmask}", strict=False)
        return network.prefixlen
    except ValueError as exc:
        logger.debug("Invalid subnet mask %r: %s", netmask, exc)
        return None


def calculate_cidr(ip_address: str, netmask: str) -> Optional[str]:
    """
    Calculate the network CIDR block for a host address and subnet mask.

    Parameters
    ----------
    ip_address:
        Host IPv4 address (e.g. ``'192.168.1.5'``).
    netmask:
        Dotted-decimal subnet mask (e.g. ``'255.255.255.0'``).

    Returns
    -------
    str or None
        CIDR string such as ``'192.168.1.0/24'``, or *None* on error.

    Examples
    --------
    >>> calculate_cidr('192.168.1.5', '255.255.255.0')
    '192.168.1.0/24'
    >>> calculate_cidr('10.0.0.42', '255.255.0.0')
    '10.0.0.0/16'
    """
    try:
        network = ipaddress.IPv4Network(
            f"{ip_address}/{netmask}", strict=False
        )
        return str(network)
    except ValueError as exc:
        logger.warning(
            "Cannot calculate CIDR for ip=%r mask=%r: %s", ip_address, netmask, exc
        )
        return None


# ---------------------------------------------------------------------------
# Default gateway detection (Windows)
# ---------------------------------------------------------------------------

#: Regex to extract an IPv4 gateway from ``route print`` output.
_GATEWAY_RE = re.compile(
    r"^\s*0\.0\.0\.0\s+0\.0\.0\.0\s+(\d{1,3}(?:\.\d{1,3}){3})",
    re.MULTILINE,
)


def _get_gateway_windows() -> Optional[str]:
    """
    Parse the Windows routing table to find the default gateway.

    Uses ``route print 0.0.0.0`` — no admin privileges required.
    Returns the first (lowest-metric) default gateway found, or *None*.
    """
    try:
        result = subprocess.run(
            ["route", "print", "0.0.0.0"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        output = result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
        logger.warning("'route print' failed: %s", exc)
        return None

    matches = _GATEWAY_RE.findall(output)
    if matches:
        gw = matches[0]
        logger.debug("Default gateway from routing table: %s", gw)
        return gw

    logger.warning("No default gateway entry found in routing table.")
    return None


def get_default_gateway() -> Optional[str]:
    """
    Return the IPv4 address of the default gateway.

    Attempts Windows ``route print`` first; logs a warning on failure.
    """
    gateway = _get_gateway_windows()
    if gateway is None:
        logger.warning("Could not determine the default gateway.")
    return gateway


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------


def get_network_config(preferred_interface: str = "") -> Optional[NetworkConfig]:
    """
    Build a complete :class:`NetworkConfig` for the best available interface.

    Parameters
    ----------
    preferred_interface:
        Optional interface name to prefer.  Passed through to
        :func:`~scanner.interface.get_preferred_interface`.

    Returns
    -------
    NetworkConfig or None
        A populated config object, or *None* if no suitable interface was
        found.  Individual fields may be *None* when their value could not
        be determined — the config is never silently dropped.
    """
    iface: Optional[InterfaceInfo] = get_preferred_interface(preferred_interface)

    if iface is None:
        logger.error(
            "No suitable active network interface found. "
            "Check that at least one network adapter is enabled."
        )
        return None

    logger.info("Building network config for interface: %s", iface.name)

    ip_address = iface.ipv4_address
    subnet_mask = iface.ipv4_netmask
    gateway = get_default_gateway()

    cidr: Optional[str] = None
    prefix_length: Optional[int] = None

    if ip_address and subnet_mask:
        cidr = calculate_cidr(ip_address, subnet_mask)
        prefix_length = netmask_to_prefix_length(subnet_mask)
    else:
        missing = []
        if not ip_address:
            missing.append("IPv4 address")
        if not subnet_mask:
            missing.append("subnet mask")
        logger.warning(
            "Missing %s for interface %r; CIDR cannot be calculated.",
            " and ".join(missing),
            iface.name,
        )

    config = NetworkConfig(
        interface_name=iface.name,
        ip_address=ip_address,
        subnet_mask=subnet_mask,
        gateway=gateway,
        cidr=cidr,
        prefix_length=prefix_length,
    )

    if config.is_complete:
        logger.info("Network config: %s", config)
    else:
        logger.warning("Network config is incomplete: %s", config)

    return config


def get_all_network_configs() -> list[NetworkConfig]:
    """
    Return :class:`NetworkConfig` objects for **every** active interface.

    Useful for multi-homed hosts.  Each entry is built independently;
    the default gateway is shared (it is host-level, not per-interface).
    """
    active_interfaces = list_active_interfaces()
    if not active_interfaces:
        logger.warning("No active interfaces found; returning empty list.")
        return []

    gateway = get_default_gateway()
    configs: list[NetworkConfig] = []

    for iface in active_interfaces:
        ip_address = iface.ipv4_address
        subnet_mask = iface.ipv4_netmask

        cidr = calculate_cidr(ip_address, subnet_mask) if ip_address and subnet_mask else None
        prefix_length = netmask_to_prefix_length(subnet_mask) if subnet_mask else None

        configs.append(
            NetworkConfig(
                interface_name=iface.name,
                ip_address=ip_address,
                subnet_mask=subnet_mask,
                gateway=gateway,
                cidr=cidr,
                prefix_length=prefix_length,
            )
        )

    logger.info(
        "Built %d network config(s): %s",
        len(configs),
        [str(c) for c in configs],
    )
    return configs
