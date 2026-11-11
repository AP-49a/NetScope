# NetScope — Development Roadmap

## Milestone Overview

| Phase | Title | Status |
|---|---|---|
| **1** | Environment Setup & Project Architecture | ✅ Complete |
| 2 | Network Discovery Engine | 🔲 Planned |
| 3 | REST API & Flask Backend | 🔲 Planned |
| 4 | Frontend UI | 🔲 Planned |
| 5 | Persistent History & Database | 🔲 Planned |
| 6 | Polish & Production Hardening | 🔲 Planned |

---

## Phase 1 — Environment Setup & Project Architecture ✅

**Goal:** A solid, tested foundation with no premature implementation.

**Deliverables:**
- Python 3.14 virtual environment
- Full project directory structure
- `config.py` — env-based centralised configuration
- `utils/logger.py` — rotating file + console logger
- `scanner/interface.py` — psutil interface enumeration & classification
- `scanner/network.py` — IP, subnet mask, gateway, CIDR detection
- Stubs for all Phase 2+ modules
- 57 unit tests (100% pass)
- README, architecture docs

**Known limitations (carry forward):**
- Gateway detection uses `route print`; will not work if `route.exe` is absent.
- Interface classification relies on name heuristics; exotic adapters fall back to `UNKNOWN`.
- No live scanning in this phase.

---

## Phase 2 — Network Discovery Engine 🔲

**Goal:** Discover all active devices on the local subnet using ARP.

**Prerequisites:**
- Npcap installed on the host (see README).
- Admin or Npcap group membership for raw-socket access.

**Planned work:**
- Implement `scanner/discovery.py` using Scapy ARP broadcast.
- Add device data model: IP, MAC, vendor lookup, first-seen / last-seen timestamps.
- Implement `database/db.py` SQLite schema (devices, scan_sessions).
- Implement `database/models.py` row mappers.
- Write integration tests with mocked Scapy.

**Interface contracts (locked in Phase 1):**
```python
# scanner/discovery.py
def scan_network(cidr: str) -> list[dict]:
    """Return list of {ip, mac, hostname} dicts."""
```

---

## Phase 3 — REST API & Flask Backend 🔲

**Goal:** Expose network data as a JSON API consumed by the browser.

**Planned endpoints:**
```
GET  /api/network/config      Current network configuration
GET  /api/interfaces          All active interfaces
POST /api/scan/start          Trigger a new ARP scan
GET  /api/scan/results        Latest scan results
GET  /api/devices             All known devices (paginated)
GET  /api/devices/<ip>        Device detail
```

**Work:**
- Implement `api/routes.py` Blueprint.
- Register Blueprint in `app.py` factory.
- Add request validation and consistent error envelope `{error, code}`.
- Add rate limiting for scan endpoints.

---

## Phase 4 — Frontend UI 🔲

**Goal:** A clean, responsive browser UI for device discovery and monitoring.

**Planned features:**
- Network overview card (interface, IP, CIDR, gateway).
- Scan button with live progress indicator.
- Device table with IP, MAC, vendor, hostname, last-seen.
- Filter and sort controls.
- Auto-refresh on a configurable interval.

**Technology:** Vanilla JS + CSS (no bundler, no framework).

---

## Phase 5 — Persistent History & Database 🔲

**Goal:** Store discovery history so device changes are tracked over time.

**Planned work:**
- Schema: `devices`, `scan_sessions`, `scan_results`.
- Track device first-seen / last-seen / status changes.
- History view in the UI.
- Simple CSV export.

---

## Phase 6 — Polish & Production Hardening 🔲

**Goal:** Make the app reliable for daily home-network use.

**Planned work:**
- Scheduled background scanning (APScheduler).
- Desktop notification on new device found.
- Configurable scan interval.
- README instructions for running as a Windows service.
- Comprehensive logging and error reporting.
- End-to-end test suite.
