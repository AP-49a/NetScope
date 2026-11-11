"""
scanner/discovery.py — ARP-based local network device discovery engine.

Uses Scapy to broadcast ARP 'who-has' requests over the target CIDR range,
collects replies, extracts IP and MAC addresses, resolves hostnames, and
identifies hardware manufacturers via MAC OUI lookups.
"""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from scapy.all import ARP, Ether, srp  # type: ignore[import-untyped]

from config import SCAN_TIMEOUT
from scanner.hostname import resolve_hostname
from scanner.network import get_network_config
from scanner.oui import get_manufacturer
from utils.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------


@dataclass
class DiscoveredDevice:
    """Represents a single active device discovered on the network."""

    ip_address: str
    """IPv4 address of the responding device."""

    mac_address: str
    """Hardware MAC address of the device."""

    hostname: Optional[str] = None
    """Resolved PTR / NetBIOS hostname, or None if unresolvable."""

    manufacturer: Optional[str] = None
    """Hardware manufacturer determined from MAC OUI prefix, or None."""

    status: str = "online"
    """Device status indicator (default: 'online')."""

    def to_dict(self) -> dict[str, Any]:
        """Convert device record to a serializable dictionary."""
        return asdict(self)


@dataclass
class ScanResult:
    """Summary and payload of a network discovery scan execution."""

    cidr: str
    """Scanned network CIDR range (e.g. '192.168.1.0/24')."""

    interface_name: str
    """Network interface adapter used for packet transmission."""

    devices: list[DiscoveredDevice] = field(default_factory=list)
    """List of all responding devices identified during the scan."""

    duration_seconds: float = 0.0
    """Elapsed scan execution time in seconds."""

    started_at: str = ""
    """ISO 8601 UTC timestamp marking scan initiation."""

    completed_at: str = ""
    """ISO 8601 UTC timestamp marking scan termination."""

    success: bool = True
    """True if scan completed without fatal driver/permission errors."""

    error_message: Optional[str] = None
    """Descriptive error message if scan failed."""

    @property
    def device_count(self) -> int:
        """Total number of discovered devices."""
        return len(self.devices)

    def to_dict(self) -> dict[str, Any]:
        """Convert scan result to a serializable dictionary."""
        return {
            "cidr": self.cidr,
            "interface_name": self.interface_name,
            "device_count": self.device_count,
            "devices": [dev.to_dict() for dev in self.devices],
            "duration_seconds": round(self.duration_seconds, 3),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "success": self.success,
            "error_message": self.error_message,
        }


# ---------------------------------------------------------------------------
# Core Discovery Engine
# ---------------------------------------------------------------------------


def scan_network(
    cidr: Optional[str] = None,
    interface_name: Optional[str] = None,
    timeout: Optional[float] = None,
    resolve_hostnames: bool = True,
) -> ScanResult:
    """
    Perform an ARP-based broadcast scan across the target CIDR block.

    Parameters
    ----------
    cidr : Optional[str]
        Target subnet CIDR (e.g. ``'192.168.1.0/24'``). If None, automatically
        detected using :func:`scanner.network.get_network_config`.
    interface_name : Optional[str]
        Name of adapter to bind for packet sending. If None, uses active adapter.
    timeout : Optional[float]
        Seconds to wait for ARP replies (default: `config.SCAN_TIMEOUT`).
    resolve_hostnames : bool
        Whether to attempt reverse DNS resolution for discovered IPs (default: True).

    Returns
    -------
    ScanResult
        Structured scan results including discovered device records, metrics,
        and execution state. Never raises unhandled exceptions.
    """
    start_wall = datetime.now(timezone.utc).isoformat()
    start_perf = time.perf_counter()

    scan_timeout = float(timeout if timeout is not None else SCAN_TIMEOUT)

    # 1. Resolve network configuration if not explicitly provided
    target_cidr = cidr
    target_iface = interface_name

    if not target_cidr or not target_iface:
        active_config = get_network_config()
        if not active_config or not active_config.cidr:
            duration = time.perf_counter() - start_perf
            error = (
                "Unable to start scan: no active network interface or valid CIDR detected. "
                "Ensure network adapter is connected."
            )
            logger.error(error)
            return ScanResult(
                cidr=target_cidr or "unknown",
                interface_name=target_iface or "unknown",
                duration_seconds=duration,
                started_at=start_wall,
                completed_at=datetime.now(timezone.utc).isoformat(),
                success=False,
                error_message=error,
            )

        target_cidr = target_cidr or active_config.cidr
        target_iface = target_iface or active_config.interface_name

    logger.info(
        "Starting ARP discovery on target=%s using interface=%s (timeout=%.1fs)",
        target_cidr,
        target_iface,
        scan_timeout,
    )

    devices: list[DiscoveredDevice] = []

    try:
        # 2. Craft ARP broadcast frame
        # Ether dst ff:ff:ff:ff:ff:ff ensures layer 2 broadcast
        # ARP pdst target_cidr specifies scan subnet
        broadcast_packet = Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=target_cidr)

        # 3. Transmit and receive packets
        # srp sends and receives packets at layer 2
        answered, _ = srp(
            broadcast_packet,
            timeout=scan_timeout,
            iface=target_iface,
            verbose=False,
            retry=1,
        )

        logger.debug("Received %d raw ARP responses", len(answered))

        # 4. Parse responses
        # answered contains list of tuples: (sent_packet, received_packet)
        for _, received in answered:
            ip = str(received[ARP].psrc).strip()
            mac = str(received[ARP].hwsrc).strip().upper()

            # Identify manufacturer via OUI
            vendor = get_manufacturer(mac)

            # Optional hostname resolution
            hostname = resolve_hostname(ip, timeout=1.0) if resolve_hostnames else None

            device = DiscoveredDevice(
                ip_address=ip,
                mac_address=mac,
                hostname=hostname,
                manufacturer=vendor,
                status="online",
            )
            devices.append(device)
            logger.debug("Discovered device: %s (%s)", ip, mac)

        duration = time.perf_counter() - start_perf
        end_wall = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Scan completed in %.3fs: discovered %d active device(s)",
            duration,
            len(devices),
        )

        return ScanResult(
            cidr=target_cidr,
            interface_name=target_iface,
            devices=devices,
            duration_seconds=duration,
            started_at=start_wall,
            completed_at=end_wall,
            success=True,
        )

    except PermissionError as exc:
        duration = time.perf_counter() - start_perf
        error_msg = (
            "Permission denied: Scapy packet capture requires Administrator privileges "
            "or membership in the 'Npcap Users' group on Windows."
        )
        logger.error("%s Detail: %s", error_msg, exc)
        return ScanResult(
            cidr=target_cidr,
            interface_name=target_iface,
            duration_seconds=duration,
            started_at=start_wall,
            completed_at=datetime.now(timezone.utc).isoformat(),
            success=False,
            error_message=error_msg,
        )
    except Exception as exc:
        duration = time.perf_counter() - start_perf
        error_msg = f"Network scan failed: {exc}"
        logger.error(error_msg, exc_info=True)
        return ScanResult(
            cidr=target_cidr,
            interface_name=target_iface,
            duration_seconds=duration,
            started_at=start_wall,
            completed_at=datetime.now(timezone.utc).isoformat(),
            success=False,
            error_message=error_msg,
        )
