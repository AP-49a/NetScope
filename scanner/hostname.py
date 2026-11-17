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


def resolve_hostnames_batch(
    ips: list[str],
    timeout: float = 1.0,
    max_workers: int = 16,
) -> dict[str, Optional[str]]:
    """
    Resolve hostnames concurrently across a collection of IP addresses.

    Executes reverse DNS PTR lookups in parallel threads so that multiple
    unresponsive devices do not serialize latency.

    Parameters
    ----------
    ips : list[str]
        List of IPv4 address strings.
    timeout : float
        Timeout per lookup in seconds (default: 1.0s).
    max_workers : int
        Maximum concurrent worker threads (default: 16).

    Returns
    -------
    dict[str, Optional[str]]
        Mapping of IP address -> resolved hostname (or None).
    """
    if not ips:
        return {}

    unique_ips = list(set(ips))
    results: dict[str, Optional[str]] = {}

    # Shortcut for loopback
    for ip in unique_ips:
        if ip == "127.0.0.1":
            results[ip] = "localhost"

    remaining = [ip for ip in unique_ips if ip not in results]
    if not remaining:
        return results

    worker_count = min(max(len(remaining), 1), max_workers)
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        future_to_ip = {executor.submit(_reverse_lookup, ip): ip for ip in remaining}

        done, not_done = concurrent.futures.wait(
            future_to_ip.keys(),
            timeout=timeout,
            return_when=concurrent.futures.ALL_COMPLETED,
        )

        for future in done:
            ip = future_to_ip[future]
            try:
                results[ip] = future.result()
            except Exception as exc:
                logger.debug("Hostname resolution failed for %s: %s", ip, exc)
                results[ip] = None

        for future in not_done:
            ip = future_to_ip[future]
            logger.debug("Hostname resolution timed out for %s after %.1fs", ip, timeout)
            results[ip] = None

    return results


def resolve_hostname(ip: str, timeout: float = 1.0) -> Optional[str]:
    """
    Attempt to resolve the PTR hostname for a single IPv4 address.

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

    res = resolve_hostnames_batch([ip], timeout=timeout)
    return res.get(ip)
