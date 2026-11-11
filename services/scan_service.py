"""
services/scan_service.py — Thread-safe scan orchestration and state management.

Coordinates background network scanning operations, enforces concurrency locks,
tracks scan execution state, and persists discovered devices and scan sessions.
"""

from __future__ import annotations

import threading
from enum import Enum
from typing import Any, Optional

from database.db import init_db
from database.models import (
    get_all_devices,
    mark_unseen_devices_offline,
    record_scan_session,
    upsert_device,
)
from scanner.discovery import ScanResult, scan_network
from utils.logger import get_logger

logger = get_logger(__name__)


class ScanState(str, Enum):
    """Operational state of the scanning engine."""

    IDLE = "idle"
    SCANNING = "scanning"
    COMPLETED = "completed"
    ERROR = "error"


class ScanService:
    """
    Orchestrates network discovery scans with thread-safe concurrency controls
    and persistent SQLite storage.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: ScanState = ScanState.IDLE
        self._latest_result: Optional[ScanResult] = None
        self._error_message: Optional[str] = None
        self._active_thread: Optional[threading.Thread] = None

        # Ensure database is initialized
        try:
            init_db()
        except Exception as exc:
            logger.warning("Database initialization deferred: %s", exc)

    @property
    def is_scanning(self) -> bool:
        """True when a scan operation is currently active."""
        return self._state == ScanState.SCANNING

    def start_scan(
        self,
        cidr: Optional[str] = None,
        interface_name: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> tuple[bool, str]:
        """
        Initiate an asynchronous scan if no scan is currently active.
        """
        acquired = self._lock.acquire(blocking=False)
        if not acquired:
            logger.warning("Rejected scan request: scan already in progress")
            return False, "A network scan is currently in progress."

        self._state = ScanState.SCANNING
        self._error_message = None

        logger.info("Spawning background thread for network scan (target=%s)", cidr or "auto")

        self._active_thread = threading.Thread(
            target=self._run_scan_worker,
            args=(cidr, interface_name, timeout),
            daemon=True,
            name="NetScope-ScanWorker",
        )
        self._active_thread.start()

        return True, "Scan initiated successfully."

    def _run_scan_worker(
        self,
        cidr: Optional[str],
        interface_name: Optional[str],
        timeout: Optional[float],
    ) -> None:
        """Worker executed in background daemon thread."""
        try:
            logger.debug("Scan worker thread started")
            result: ScanResult = scan_network(
                cidr=cidr,
                interface_name=interface_name,
                timeout=timeout,
            )
            self._latest_result = result

            if result.success:
                # 1. Persist responding devices into database
                active_macs: list[str] = []
                device_ids: list[int] = []

                for dev in result.devices:
                    active_macs.append(dev.mac_address)
                    dev_id = upsert_device(
                        mac_address=dev.mac_address,
                        ip_address=dev.ip_address,
                        hostname=dev.hostname,
                        manufacturer=dev.manufacturer,
                        status="online",
                    )
                    device_ids.append(dev_id)

                # 2. Mark previously seen devices that did not respond as offline
                mark_unseen_devices_offline(active_macs)

                # 3. Record scan session and link observed devices
                record_scan_session(result, device_ids)

                self._state = ScanState.COMPLETED
                logger.info(
                    "Background scan completed and saved: %d devices active",
                    len(result.devices),
                )
            else:
                self._state = ScanState.ERROR
                self._error_message = result.error_message
                record_scan_session(result)
                logger.error("Background scan finished with error: %s", result.error_message)

        except Exception as exc:
            self._state = ScanState.ERROR
            self._error_message = f"Unexpected scan worker exception: {exc}"
            logger.error("Scan worker crashed: %s", exc, exc_info=True)
        finally:
            self._lock.release()
            logger.debug("Scan worker thread finished; lock released")

    def get_status(self) -> dict[str, Any]:
        """Return the current operational state and metrics."""
        return {
            "status": self._state.value,
            "is_scanning": self.is_scanning,
            "last_scan": self._latest_result.to_dict() if self._latest_result else None,
            "error_message": self._error_message,
        }

    def get_devices(self, status_filter: Optional[str] = None) -> list[dict[str, Any]]:
        """
        Return device records from persistent database storage.
        """
        try:
            return get_all_devices(status_filter=status_filter)
        except Exception as exc:
            logger.error("Failed to query devices from database: %s", exc)
            return []

    def reset_state_for_testing(self) -> None:
        """Reset internal state (for hermetic test execution)."""
        if self._lock.locked():
            try:
                self._lock.release()
            except RuntimeError:
                pass
        self._state = ScanState.IDLE
        self._latest_result = None
        self._error_message = None
        self._active_thread = None


# Global singleton service instance
scan_service = ScanService()
