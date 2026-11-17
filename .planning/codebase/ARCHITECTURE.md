# NetScope — Architecture & System Design

## 1. Architectural Overview

NetScope follows a clean, modular layered architecture that separates network low-level packet capture, thread-safe service coordination, persistent data storage, REST API routing, and browser presentation.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Browser Presentation                          │
│                   (HTML5 / CSS3 / Vanilla JavaScript)                   │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │ HTTP (127.0.0.1:5000)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   Flask Application & REST API Layer                    │
│      • app.py (create_app factory)                                      │
│      • api/routes.py (GET /api/network, POST /api/scan, etc.)          │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Application Service Layer                        │
│      • services/scan_service.py (ScanService singleton)                 │
│      • Threading Lock (Single-Writer Mutual Exclusion)                  │
│      • Background Daemon Worker Threading                               │
└──────────────────┬───────────────────────────────────┬──────────────────┘
                   │                                   │
                   ▼                                   ▼
┌────────────────────────────────────┐ ┌──────────────────────────────────┐
│        Scanner Engine Layer        │ │       Database Storage Layer     │
│ ────────────────────────────────── │ │ ──────────────────────────────── │
│ • scanner/interface.py (psutil)    │ │ • database/db.py (SQLite WAL)    │
│ • scanner/network.py (ipaddress)   │ │ • database/models.py (ORM/DAL)   │
│ • scanner/discovery.py (Scapy ARP) │ │   - devices (table)              │
│ • scanner/oui.py (OUI Vendor Map)  │ │   - scan_history (table)         │
│ • scanner/hostname.py (Reverse DNS)│ │   - scan_results (join table)    │
└────────────────────────────────────┘ └──────────────────────────────────┘
```

---

## 2. Component Details

### 2.1 Launcher & Diagnostics (`run.py`, `run.bat`)
- Acts as the primary entry point on Windows 11.
- Performs diagnostic preflight checks:
  1. Python version verification (`>= 3.11`).
  2. Dependency verification (`flask`, `psutil`, `scapy`, `dotenv`).
  3. Database initialization (`init_db()`).
  4. Scapy & Windows Administrator privilege inspection.
- Prints a structured startup console banner and launches the Flask WSGI server.

### 2.2 Scanner Engine (`scanner/`)
- **`scanner/interface.py`**:
  - Discovers all network adapters via `psutil`.
  - Determines operational state, IP/MAC addresses, and classifies adapter types (`WIFI`, `ETHERNET`, `LOOPBACK`, `VIRTUAL`, `UNKNOWN`).
  - Prioritizes physical adapters over virtual or loopback interfaces.
- **`scanner/network.py`**:
  - Calculates IPv4 network address and prefix lengths using Python's `ipaddress` library.
  - Resolves upstream default gateway router by querying Windows routing tables.
- **`scanner/discovery.py`**:
  - Performs ARP broadcast discovery using Scapy `srp()`.
  - Automatically enriches hostnames for known network roles:
    - Default gateway IP marked as `Router (Default Gateway)`.
    - Local host IP marked with `(This PC)`.
  - Identifies hardware manufacturers via OUI prefix matching or tags randomized MAC addresses.
- **`scanner/oui.py`**:
  - Offline IEEE MAC OUI database with normalization heuristics.
  - Inspects IEEE 802 Locally Administered Address (LAA) bits to identify randomized private MAC addresses.
- **`scanner/hostname.py`**:
  - Non-blocking reverse DNS lookups executed in a bounded thread pool with a 1.0-second timeout.

### 2.3 Service Layer (`services/`)
- **`services/scan_service.py`**:
  - Coordinates scan execution using a state machine (`IDLE` &rarr; `SCANNING` &rarr; `COMPLETED` / `ERROR`).
  - Enforces single-writer mutual exclusion via `threading.Lock`: only one scan may execute at a time (concurrent requests receive `409 Conflict`).
  - Executes scans in a background daemon thread so the API responds with `202 Accepted` immediately without blocking the web server.
  - Automatically handles database persistence upon scan completion.

### 2.4 Persistence Layer (`database/`)
- **`database/db.py`**:
  - Context manager `get_db_connection()` providing connections with `sqlite3.Row` dict-like access.
  - Configures SQLite Write-Ahead Logging (`WAL` mode) and foreign key constraints (`PRAGMA foreign_keys = ON`).
  - Idempotent schema initialization (`init_db()`) and automatic column migrations.
- **`database/models.py`**:
  - `upsert_device()`: Inserts newly discovered devices or updates IP, last seen, and status while strictly preserving the initial `first_seen` timestamp and any user-assigned custom nickname.
  - `set_device_custom_name()`: Allows users to assign friendly labels/nicknames to tracked devices.
  - `mark_unseen_devices_offline()`: Gracefully transitions absent devices to `offline` status without data loss.
  - `record_scan_session()`: Persists audit sessions in `scan_history` and links device observations in `scan_results`.

### 2.5 REST API Layer (`api/`)
- **`api/routes.py`**: Flask Blueprint registering endpoints:
  - `GET /`: Serves the single-page application dashboard.
  - `GET /api/network`: Introspects active adapter and subnet configuration.
  - `POST /api/scan`: Initiates background ARP sweep (with defensive CIDR and timeout validation).
  - `GET /api/status`: Real-time scan progress, duration, and error reporting.
  - `GET /api/devices`: Serves tracked devices with optional status filtering.
  - `PATCH /api/devices/<mac>`: Updates user-assigned custom friendly nicknames.
  - `GET /api/history`: Serves historical scan session audit logs.

### 2.6 Frontend Layer (`templates/` & `static/`)
- **`templates/index.html`**: Semantic HTML5 dashboard structure.
- **`static/css/style.css`**: Utility dark-theme CSS with custom properties and responsive layout.
- **`static/js/app.js`**: Pure client-side JavaScript managing polling loops, instant substring filtering, DOM table rendering, and inline device renaming.
