# NetScope — Architecture Documentation

## 1. Project Overview

NetScope is a local-first network discovery and device monitoring web application designed specifically for Windows 11. It allows users to inspect their local network interfaces, broadcast ARP discovery queries, identify connected devices with MAC OUI manufacturer lookups and reverse DNS hostnames, inspect device availability, and maintain historical scan logs in an SQLite database.

---

## 2. System Architecture

```
                       ┌────────────────────────────────────────────────────────┐
                       │                   Browser Client                       │
                       │           (HTML5 / CSS3 / Vanilla JavaScript)          │
                       └───────────────────────────┬────────────────────────────┘
                                                   │ HTTP / JSON
                                                   ▼
                       ┌────────────────────────────────────────────────────────┐
                       │               Flask Application (app.py)               │
                       │             API Blueprint (api/routes.py)              │
                       └─────────────┬────────────────────────────┬─────────────┘
                                     │                            │
                                     ▼                            ▼
                 ┌──────────────────────────────────────┐  ┌─────────────┐
                 │     Scan Service (Thread Lock)       │  │ Static & UI │
                 │      (services/scan_service.py)      │  │ (Templates) │
                 └──────────────────┬───────────────────┘  └─────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │        Scanner Engine Layer          │
                 │ ──────────────────────────────────── │
                 │ • scanner/interface.py (psutil)      │
                 │ • scanner/network.py (ipaddress)     │
                 │ • scanner/discovery.py (Scapy ARP)   │
                 │ • scanner/oui.py (OUI Vendor Map)    │
                 │ • scanner/hostname.py (Reverse DNS)  │
                 └──────────────────┬───────────────────┘
                                    │
                                    ▼
                 ┌──────────────────────────────────────┐
                 │       Database Persistence           │
                 │ ──────────────────────────────────── │
                 │ • database/db.py (SQLite WAL mode)   │
                 │ • database/models.py (Data Models)   │
                 │   - devices                          │
                 │   - scan_history                     │
                 │   - scan_results                     │
                 └──────────────────────────────────────┘
```

---

## 3. Module Reference

### 3.1 Application & Launcher Layer
- **`run.py`**: Production launcher executing diagnostic preflights:
  - Verifies Python version (`sys.version_info >= (3, 11)`).
  - Verifies presence of core libraries (`flask`, `psutil`, `scapy`, `dotenv`).
  - Checks Windows Administrator privileges for raw ARP packet capture.
  - Automatically initializes SQLite database schema.
  - Starts Flask server on `http://127.0.0.1:5000`.
- **`run.bat`**: Windows batch wrapper for double-click startup.
- **`app.py`**: Flask application factory (`create_app()`) registering routes and configuration.
- **`config.py`**: Centralized configuration reading from `.env` with fallback defaults.

### 3.2 Scanner Engine (`scanner/`)
- **`scanner/interface.py`**: Interface enumeration via `psutil`. Classifies interfaces (`WIFI`, `ETHERNET`, `LOOPBACK`, `VIRTUAL`, `UNKNOWN`) and selects highest priority active physical interface.
- **`scanner/network.py`**: IPv4 subnet calculations (`ipaddress`), netmask-to-prefix translation, and default gateway resolution parsing `route print 0.0.0.0`.
- **`scanner/discovery.py`**: Scapy-based ARP broadcast engine (`Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=cidr)`). Returns typed `DiscoveredDevice` and `ScanResult` instances with duration and status metrics.
- **`scanner/oui.py`**: Offline MAC Organizationally Unique Identifier (OUI) lookup matching normalized MAC prefixes (e.g., `00:1A:2B`) against known hardware vendors.
- **`scanner/hostname.py`**: Non-blocking reverse DNS hostname resolver with thread-bounded timeouts to avoid stalling network sweeps.

### 3.3 Application Services (`services/`)
- **`services/scan_service.py`**: Singleton state coordinator:
  - Uses `threading.Lock` to enforce single-writer mutual exclusion, preventing concurrent conflicting ARP sweeps.
  - Spawns background daemon worker threads for asynchronous scanning.
  - Manages scanning state transitions (`idle` → `scanning` → `completed` / `error`).
  - Automatically persists scan sessions and discovered devices to SQLite.

### 3.4 Data Access & Persistence (`database/`)
- **`database/db.py`**: Connection pool management and schema initialization:
  - SQLite Write-Ahead Logging (`PRAGMA journal_mode = WAL`) for concurrent read performance.
  - Foreign key enforcement (`PRAGMA foreign_keys = ON`).
  - Safe transaction context manager with automatic commit on success and rollback on exceptions.
- **`database/models.py`**: Data access functions:
  - `upsert_device()`: Inserts newly discovered devices or updates IP, last seen, and manufacturer while strictly preserving the initial `first_seen` timestamp.
  - `mark_unseen_devices_offline()`: Gracefully transitions absent devices to `offline` status without data loss.
  - `record_scan_session()`: Persists audit sessions in `scan_history` and links device observations in `scan_results`.
  - `get_all_devices()`, `get_scan_history()`: Structured query accessors.

### 3.5 REST API Layer (`api/`)
- **`api/routes.py`**: Flask Blueprint defining JSON endpoints:
  - `GET /`: Serves the dashboard HTML.
  - `GET /api/network`: Returns active network interface, host IP, mask, and CIDR.
  - `POST /api/scan`: Accepts optional target CIDR (validated via `ipaddress`) and timeout; triggers asynchronous background scan.
  - `GET /api/status`: Returns current scanner progress and latest metrics.
  - `GET /api/devices`: Serves complete inventory of tracked devices with status filters.
  - `GET /api/history`: Returns historical scan sessions.

### 3.6 Frontend Client (`templates/` & `static/`)
- **`templates/index.html`**: Semantic, accessible HTML5 dashboard structure with network overview, action toolbar, device inventory table, and historical log modal.
- **`static/css/style.css`**: Responsive dark theme stylesheet with CSS custom properties, monospace tabular data alignment, and status badge styling.
- **`static/js/app.js`**: Vanilla JavaScript client controller featuring async fetch calls, poll loops during scans, real-time client-side search filtering, and error handling.

---

## 4. Concurrency & Thread-Safety Model

1. **Single-Writer Mutual Exclusion**:
   - Only one active ARP scan is permitted at any given time.
   - When a scan is running, `POST /api/scan` returns `409 Conflict` (`Scan in progress`).
2. **Background Daemon Threading**:
   - Scans run in a separate daemon thread to ensure the Flask HTTP request thread returns immediately with `202 Accepted`.
3. **SQLite WAL Concurrency**:
   - Write-Ahead Logging allows continuous reads (`GET /api/devices`) even while background scans are writing results to the database.
