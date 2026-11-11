"""
scanner/hostname.py — Hostname resolution with strict timeout bounds.

Performs reverse DNS lookups (IP -> Hostname) using standard system resolver
with bounded timeout to prevent network operations from hanging.
"""

from __future__ import annotations

import concurrent.futures
import socket
from typing import Optional

from utils.logger import get_logger

logger = get_logger(__name__)


def _reverse_lookup(ip: str) -> Optional[str]:
    """Internal blocking reverse DNS call."""
    try:
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname.strip() or None
    except (socket.herror, socket.gaierror, socket.timeout, OSError) as exc:
        logger.debug("Failed to resolve hostname for %s: %s", ip, exc)
        return None


def resolve_hostname(ip: str, timeout: float = 1.0) -> Optional[str]:
    """
    Attempt to resolve the PTR hostname for an IPv4 address.

    Parameters
    ----------
    ip : str
        IPv4 address string (e.g. ``'192.168.1.1'``).
    timeout : float
        Maximum wait time in seconds before abandoning lookup (default: 1.0s).

    Returns
    -------
    Optional[str]
        Resolved hostname string, or None if unresolvable or timed out.
    """
    if not ip or not isinstance(ip, str):
        return None

    # Handle loopback immediately
    if ip == "127.0.0.1":
        return "localhost"

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_reverse_lookup, ip)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            logger.debug("Hostname resolution timed out for %s after %.1fs", ip, timeout)
            return None
        except Exception as exc:
            logger.debug("Unexpected error resolving hostname for %s: %s", ip, exc)
            return None
