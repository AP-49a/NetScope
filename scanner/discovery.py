"""
scanner/discovery.py — Device discovery stub.

This module is reserved for Phase 2 (ARP-based device discovery using Scapy).
No scanning logic is implemented here in Phase 1.
"""

from __future__ import annotations

from utils.logger import get_logger

logger = get_logger(__name__)


def scan_network(cidr: str) -> list[dict]:  # noqa: ARG001
    """
    Scan the given CIDR range for active devices.

    .. note::
        **Not implemented in Phase 1.**  Returns an empty list and logs
        a warning.  ARP scanning requires Npcap on Windows and will be
        implemented in Phase 2.

    Parameters
    ----------
    cidr:
        Network in CIDR notation, e.g. ``'192.168.1.0/24'``.

    Returns
    -------
    list[dict]
        Empty list in Phase 1.
    """
    logger.warning(
        "scan_network() called but device discovery is not implemented until Phase 2. "
        "CIDR=%r",
        cidr,
    )
    return []
