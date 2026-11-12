"""
database/models.py — Data access operations and device lifecycle tracking.

Implements database operations for saving discovered devices, preserving
historical first_seen timestamps, tracking offline state transitions,
and recording audit trails of scan sessions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from database.db import get_db_connection
from scanner.discovery import ScanResult
from utils.logger import get_logger

logger = get_logger(__name__)


def upsert_device(
    mac_address: str,
    ip_address: str,
    hostname: Optional[str] = None,
    manufacturer: Optional[str] = None,
    timestamp: Optional[str] = None,
    status: str = "online",
    custom_name: Optional[str] = None,
    db_path: Optional[Path | str] = None,
) -> int:
    """
    Insert a newly discovered device or update an existing device record.

    If the device is already in the database (matched by MAC address):
    - Updates ``last_seen``, ``ip_address``, and ``status`` to 'online'.
    - Updates ``hostname`` and ``manufacturer`` only if new values are present.
    - Preserves ``custom_name`` unless a new non-empty custom_name is provided.
    - Strictly preserves the original ``first_seen`` timestamp.

    Returns
    -------
    int
        Primary key ID of the inserted or updated device.
    """
    clean_mac = mac_address.strip().upper()
    now_ts = timestamp or datetime.now(timezone.utc).isoformat()

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM devices WHERE mac_address = ?", (clean_mac,))
        existing = cursor.fetchone()

        if existing is None:
            cursor.execute(
                """
                INSERT INTO devices (
                    mac_address, ip_address, hostname, custom_name, manufacturer,
                    first_seen, last_seen, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (clean_mac, ip_address, hostname, custom_name, manufacturer, now_ts, now_ts, status),
            )
            device_id = cursor.lastrowid
            logger.debug("Inserted new device into database: %s (id=%d)", clean_mac, device_id)
            return int(device_id)

        # Update existing record while preserving original first_seen and existing custom_name
        device_id = int(existing["id"])
        final_hostname = hostname if hostname is not None else existing["hostname"]
        final_manufacturer = manufacturer if manufacturer is not None else existing["manufacturer"]
        final_custom_name = custom_name if custom_name is not None else existing["custom_name"]

        cursor.execute(
            """
            UPDATE devices SET
                ip_address = ?,
                hostname = ?,
                custom_name = ?,
                manufacturer = ?,
                last_seen = ?,
                status = ?
            WHERE id = ?
            """,
            (ip_address, final_hostname, final_custom_name, final_manufacturer, now_ts, status, device_id),
        )
        logger.debug("Updated existing device in database: %s (id=%d)", clean_mac, device_id)
        return device_id


def set_device_custom_name(
    mac_address: str,
    custom_name: Optional[str],
    db_path: Optional[Path | str] = None,
) -> bool:
    """
    Assign or update a user-defined friendly nickname for a device.

    Parameters
    ----------
    mac_address : str
        MAC address of the target device.
    custom_name : Optional[str]
        Friendly nickname (e.g. "Ankan's iPhone", "Smart TV") or None/empty to clear.

    Returns
    -------
    bool
        True if the device was found and updated, False otherwise.
    """
    clean_mac = mac_address.strip().upper()
    cleaned_name = custom_name.strip() if custom_name and custom_name.strip() else None

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE devices SET custom_name = ? WHERE mac_address = ?",
            (cleaned_name, clean_mac),
        )
        success = cursor.rowcount > 0
        if success:
            logger.info("Updated custom nickname for %s -> '%s'", clean_mac, cleaned_name)
        return success


def mark_unseen_devices_offline(
    active_macs: list[str],
    db_path: Optional[Path | str] = None,
) -> int:
    """
    Mark devices not present in the latest active scan as 'offline'.

    Parameters
    ----------
    active_macs : list[str]
        List of MAC addresses responding in the latest scan.

    Returns
    -------
    int
        Number of devices transitioned to 'offline'.
    """
    clean_macs = [mac.strip().upper() for mac in active_macs if mac]

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()

        if not clean_macs:
            cursor.execute("UPDATE devices SET status = 'offline' WHERE status = 'online'")
        else:
            placeholders = ",".join("?" for _ in clean_macs)
            cursor.execute(
                f"""
                UPDATE devices SET status = 'offline'
                WHERE status = 'online' AND mac_address NOT IN ({placeholders})
                """,
                clean_macs,
            )

        updated_count = cursor.rowcount
        logger.debug("Transitioned %d unseen devices to offline state", updated_count)
        return int(updated_count)


def record_scan_session(
    scan_result: ScanResult,
    device_ids: Optional[list[int]] = None,
    db_path: Optional[Path | str] = None,
) -> int:
    """
    Record an executed scan session and associate it with discovered devices.

    Parameters
    ----------
    scan_result : ScanResult
        Scan execution result object.
    device_ids : Optional[list[int]]
        Primary key IDs of the devices observed during this scan.

    Returns
    -------
    int
        Primary key ID of the created scan session record.
    """
    status_str = "completed" if scan_result.success else "error"

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO scan_history (
                cidr, interface_name, started_at, completed_at,
                duration_seconds, device_count, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scan_result.cidr,
                scan_result.interface_name,
                scan_result.started_at,
                scan_result.completed_at,
                scan_result.duration_seconds,
                scan_result.device_count,
                status_str,
                scan_result.error_message,
            ),
        )
        scan_id = int(cursor.lastrowid)

        # Link associated devices in scan_results join table
        if device_ids:
            records = [(scan_id, dev_id) for dev_id in device_ids]
            cursor.executemany(
                "INSERT INTO scan_results (scan_id, device_id) VALUES (?, ?)",
                records,
            )

        logger.debug("Recorded scan session #%d (devices=%d)", scan_id, scan_result.device_count)
        return scan_id


def get_all_devices(
    status_filter: Optional[str] = None,
    db_path: Optional[Path | str] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve all devices from the database ordered by last_seen descending.

    Parameters
    ----------
    status_filter : Optional[str]
        Optional filter: 'online' or 'offline'.

    Returns
    -------
    list[dict[str, Any]]
        List of device dictionaries with timestamps and attributes.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        if status_filter:
            cursor.execute(
                "SELECT * FROM devices WHERE status = ? ORDER BY last_seen DESC",
                (status_filter.lower(),),
            )
        else:
            cursor.execute("SELECT * FROM devices ORDER BY last_seen DESC")

        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_scan_history(
    limit: int = 20,
    db_path: Optional[Path | str] = None,
) -> list[dict[str, Any]]:
    """
    Retrieve recent scan history sessions.

    Parameters
    ----------
    limit : int
        Maximum number of sessions to retrieve (default: 20).

    Returns
    -------
    list[dict[str, Any]]
        List of scan history dictionaries.
    """
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM scan_history ORDER BY started_at DESC LIMIT ?",
            (limit,),
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
