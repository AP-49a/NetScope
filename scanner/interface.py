"""
scanner/interface.py — Network interface enumeration and classification.

Responsibilities (Phase 1):
  - List all network interfaces available on the host.
  - Identify which interfaces are currently active (have an IPv4 address
    and are in the UP state).
  - Classify interfaces as Wi-Fi, Ethernet, Loopback, or Virtual/Other
    based on interface name heuristics (Windows-specific).
  - Return structured InterfaceInfo objects — no network scanning.

Dependencies: psutil (standard Windows networking; no admin rights required).
"""

from __future__ import annotations

import re
import socket
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import psutil

from utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------


class InterfaceKind(str, Enum):
    """Broad classification of a network interface."""

    LOOPBACK = "loopback"
    ETHERNET = "ethernet"
    WIFI = "wifi"
    VIRTUAL = "virtual"
    UNKNOWN = "unknown"


@dataclass
class InterfaceInfo:
    """Structured summary of one network interface."""

    name: str
    """OS interface name, e.g. ``'Ethernet'`` or ``'Wi-Fi'``."""

    kind: InterfaceKind
    """Broad classification of the interface type."""

    is_up: bool
    """True when the interface reports itself as UP."""

    ipv4_address: Optional[str] = None
    """Primary IPv4 address, or *None* if not assigned."""

    ipv4_netmask: Optional[str] = None
    """IPv4 subnet mask, or *None* if not assigned."""

    mac_address: Optional[str] = None
    """MAC address string, or *None* if not available."""

    flags: list[str] = field(default_factory=list)
    """Raw ``psutil`` stat flags (e.g. ``['up', 'broadcast']``)."""

    @property
    def is_active(self) -> bool:
        """An interface is considered *active* when it is UP and has an IPv4 address."""
        return self.is_up and self.ipv4_address is not None

    def __str__(self) -> str:
        status = "active" if self.is_active else "inactive"
        return (
            f"InterfaceInfo(name={self.name!r}, kind={self.kind.value}, "
            f"status={status}, ip={self.ipv4_address})"
        )


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

#: Patterns that identify virtual / tunnel interfaces on Windows.
_VIRTUAL_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"vethernet", re.IGNORECASE),
    re.compile(r"vmware", re.IGNORECASE),
    re.compile(r"virtualbox", re.IGNORECASE),
    re.compile(r"hyper-v", re.IGNORECASE),
    re.compile(r"docker", re.IGNORECASE),
    re.compile(r"^tap", re.IGNORECASE),
    re.compile(r"^tun", re.IGNORECASE),
    re.compile(r"wsl", re.IGNORECASE),
    re.compile(r"loopback pseudo-interface", re.IGNORECASE),
]

#: Patterns that identify Wi-Fi interfaces on Windows.
_WIFI_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"wi-fi", re.IGNORECASE),
    re.compile(r"wireless", re.IGNORECASE),
    re.compile(r"wlan", re.IGNORECASE),
    re.compile(r"802\.11", re.IGNORECASE),
]

#: Patterns that identify Ethernet interfaces on Windows.
_ETHERNET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^ethernet", re.IGNORECASE),
    re.compile(r"^local area connection", re.IGNORECASE),
    re.compile(r"^eth", re.IGNORECASE),
]


def _classify_interface(name: str, is_loopback: bool) -> InterfaceKind:
    """
    Classify an interface by name and loopback flag.

    Classification priority (highest → lowest):
    1. Loopback flag from psutil stats.
    2. Virtual patterns (must be checked before Ethernet/Wi-Fi).
    3. Wi-Fi name patterns.
    4. Ethernet name patterns.
    5. Unknown.
    """
    if is_loopback:
        return InterfaceKind.LOOPBACK

    for pattern in _VIRTUAL_PATTERNS:
        if pattern.search(name):
            return InterfaceKind.VIRTUAL

    for pattern in _WIFI_PATTERNS:
        if pattern.search(name):
            return InterfaceKind.WIFI

    for pattern in _ETHERNET_PATTERNS:
        if pattern.search(name):
            return InterfaceKind.ETHERNET

    return InterfaceKind.UNKNOWN


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def list_interfaces() -> list[InterfaceInfo]:
    """
    Return a list of :class:`InterfaceInfo` for every interface on the host.

    The list includes inactive interfaces so callers can inspect the full
    picture.  Use :func:`list_active_interfaces` to filter to live ones.

    Returns
    -------
    list[InterfaceInfo]
        One entry per OS network interface, never raises.
    """
    interfaces: list[InterfaceInfo] = []

    try:
        stats: dict[str, psutil._common.snicstats] = psutil.net_if_stats()
        addrs: dict[str, list[psutil._common.snicaddr]] = psutil.net_if_addrs()
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to enumerate network interfaces: %s", exc)
        return interfaces

    for name, stat in stats.items():
        is_loopback: bool = stat.flags is not None and "loopback" in stat.flags.lower()
        kind = _classify_interface(name, is_loopback)
        is_up = bool(stat.isup)

        # Extract IPv4 address and netmask.
        ipv4_addr: Optional[str] = None
        ipv4_mask: Optional[str] = None
        mac_addr: Optional[str] = None

        for addr in addrs.get(name, []):
            if addr.family == socket.AF_INET:
                if ipv4_addr is None:  # Take the first IPv4 address.
                    ipv4_addr = addr.address
                    ipv4_mask = addr.netmask
            elif addr.family == psutil.AF_LINK:
                mac_addr = addr.address

        raw_flags = [f.strip() for f in (stat.flags or "").split(",") if f.strip()]

        iface = InterfaceInfo(
            name=name,
            kind=kind,
            is_up=is_up,
            ipv4_address=ipv4_addr,
            ipv4_netmask=ipv4_mask,
            mac_address=mac_addr,
            flags=raw_flags,
        )
        interfaces.append(iface)
        logger.debug("Enumerated interface: %s", iface)

    logger.info("Found %d network interface(s).", len(interfaces))
    return interfaces


def list_active_interfaces() -> list[InterfaceInfo]:
    """
    Return only interfaces that are UP and have an IPv4 address assigned.

    Loopback and virtual interfaces are **included** unless explicitly
    filtered by the caller.
    """
    active = [iface for iface in list_interfaces() if iface.is_active]
    logger.info(
        "Found %d active interface(s): %s",
        len(active),
        [i.name for i in active],
    )
    return active


def get_preferred_interface(preferred_name: str = "") -> Optional[InterfaceInfo]:
    """
    Return the best interface to use for network operations.

    Selection priority:
    1. The interface named *preferred_name* (if active).
    2. The first active Ethernet interface.
    3. The first active Wi-Fi interface.
    4. Any other active non-loopback, non-virtual interface.
    5. *None* if no suitable interface is found.

    Parameters
    ----------
    preferred_name:
        Optional interface name override (from config / env var).
    """
    active = list_active_interfaces()

    if not active:
        logger.warning("No active network interfaces found.")
        return None

    # 1. Honour explicit preference.
    if preferred_name:
        for iface in active:
            if iface.name.lower() == preferred_name.lower():
                logger.info("Using preferred interface: %s", iface.name)
                return iface
        logger.warning(
            "Preferred interface %r not found or inactive; falling back to auto-select.",
            preferred_name,
        )

    # 2. First active Ethernet.
    for iface in active:
        if iface.kind == InterfaceKind.ETHERNET:
            logger.info("Auto-selected Ethernet interface: %s", iface.name)
            return iface

    # 3. First active Wi-Fi.
    for iface in active:
        if iface.kind == InterfaceKind.WIFI:
            logger.info("Auto-selected Wi-Fi interface: %s", iface.name)
            return iface

    # 4. Any non-loopback, non-virtual interface.
    for iface in active:
        if iface.kind not in (InterfaceKind.LOOPBACK, InterfaceKind.VIRTUAL):
            logger.info("Auto-selected interface (fallback): %s", iface.name)
            return iface

    logger.warning("No suitable non-virtual active interface found.")
    return None
