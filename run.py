"""
run.py — Production Preflight Launcher for NetScope.

Performs environment diagnostics, database initialization, and launches
the NetScope Flask application on 127.0.0.1:5000.
"""

from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path


def check_python_version() -> None:
    """Ensure runtime meets minimum Python 3.11 requirement."""
    if sys.version_info < (3, 11):
        print(
            f"[FATAL] Python 3.11+ is required. Detected Python "
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}."
        )
        sys.exit(1)


def check_dependencies() -> None:
    """Verify required libraries are installed."""
    missing = []
    for pkg in ("flask", "psutil", "scapy", "dotenv"):
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print(f"[FATAL] Missing required packages: {', '.join(missing)}")
        print("Please install required dependencies with: pip install -r requirements.txt")
        sys.exit(1)


def is_admin() -> bool:
    """Check if process has elevated administrator privileges on Windows."""
    if os.name != "nt":
        return True
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def check_driver_readiness() -> bool:
    """Verify Npcap or packet capture drivers are accessible."""
    try:
        from scapy.arch.windows import get_windows_if_list  # type: ignore[import-untyped]
        ifs = get_windows_if_list()
        return len(ifs) > 0
    except Exception:
        return False


def print_banner(active_ip: str | None, active_cidr: str | None, is_elevated: bool) -> None:
    """Display startup diagnostics and access URL."""
    divider = "=" * 62
    print(divider)
    print("  NetScope — Local Network Discovery & Monitoring Dashboard")
    print("  Version: 1.0.0 (Release)")
    print(divider)
    print(f"  Access URL          : http://127.0.0.1:5000")
    print(f"  Active Host IP      : {active_ip or 'Detecting...'}")
    print(f"  Subnet CIDR Range   : {active_cidr or 'Detecting...'}")
    print(f"  Process Privileges  : {'Administrator (Elevated)' if is_elevated else 'Standard User'}")
    print(divider)

    if not is_elevated:
        print("  [NOTE] Scapy raw ARP packet capture on Windows 11 may require")
        print("         Administrator privileges and Npcap installed in")
        print("         WinPcap-compatible mode.")
        print("         If network scanning fails, please run terminal as Admin.")
        print(divider)

    print("  Press CTRL+C to stop the NetScope server.\n")


def main() -> None:
    """Preflight check and main application startup."""
    check_python_version()
    check_dependencies()

    # Initialize local SQLite database
    from database.db import init_db
    init_db()

    # Pre-detect active interface for banner
    active_ip = None
    active_cidr = None
    try:
        from scanner.network import get_network_config
        cfg = get_network_config()
        if cfg:
            active_ip = cfg.ip_address
            active_cidr = cfg.cidr
    except Exception:
        pass

    elevated = is_admin()
    print_banner(active_ip, active_cidr, elevated)

    # Launch Flask application
    from app import create_app
    app = create_app()

    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
