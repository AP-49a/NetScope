# Phase 7 Research: Polish, Documentation and Release

## 1. Domain & Release Engineering Analysis

### 1.1 Windows 11 Runtime Considerations
- **Raw Socket Privileges**: Scapy ARP broadcast scanning (`Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(...)`) relies on low-level packet construction and sniffing via Npcap. On Windows 11, running raw packet capture requires elevated Administrator privileges or Npcap installed with "Install Npcap in WinPcap API-compatible Mode" and restricted driver access configured properly.
- **Npcap Driver Dependency**: Without Npcap installed on Windows, Scapy raises `Scapy_Exception` or `RuntimeError`. Documentation must detail exact download instructions (`https://npcap.com/`), required installer checkboxes, and troubleshooting for driver detection errors.
- **Loopback & Local Binding**: Flask default development server runs on `127.0.0.1:5000`. In accordance with security guardrails, NetScope must only bind to `127.0.0.1` by default and never expose administrative scan controls to external networks without explicit user configuration.

### 1.2 Startup & Launcher UX
- Currently, running the app requires `python app.py`.
- To deliver a polished developer/user experience on Windows 11:
  - Create a dedicated root startup script `run.py` with diagnostic preflight checks:
    - Verifies Python version (>= 3.11).
    - Checks required dependencies (`flask`, `psutil`, `scapy`).
    - Checks Npcap presence / Scapy driver availability with helpful warnings if missing.
    - Ensures database is initialized (`database/db.py`).
    - Starts Flask on `http://127.0.0.1:5000` and displays clean console banners.
  - Create an optional Windows batch launcher `run.bat` for double-click startup.

### 1.3 Documentation & Architecture Artifacts
- **`README.md`**: Update from the Phase 1 stub into a comprehensive, production-ready product manual:
  - Hero header with badges and project purpose.
  - Features overview (Active Interface Detection, ARP Discovery, OUI Lookup, Hostname Resolution, Persistent Inventory, Scan History, Responsive Dark Dashboard).
  - Prerequisites (Windows 11, Python 3.11+, Npcap).
  - Step-by-step Setup Guide (venv setup, dependency install, `.env` config).
  - How to run NetScope (using `run.py` or `python app.py`).
  - Comprehensive API Reference (Request/response schemas for `/api/network`, `/api/scan`, `/api/status`, `/api/devices`, `/api/history`).
  - Troubleshooting & FAQ (Admin elevation, Npcap installation, missing Wi-Fi interfaces, firewall restrictions).
  - Architecture and Technology Stack.
- **`docs/architecture.md` & `docs/api.md`**:
  - Keep synchronized with Phase 1-6 changes (WAL SQLite database, scan service threading, OUI lookups).

### 1.4 Codebase Cleanup & Hygiene
- Ensure all debug prints, unused imports, or lingering artifacts are eliminated.
- Ensure `.gitignore` properly excludes `*.db`, `__pycache__`, `.coverage`, `logs/*.log`.
- Verify the entire test suite (119+ tests) runs cleanly.
