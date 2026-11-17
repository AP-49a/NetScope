# NetScope — Technology Stack

## 1. Overview
NetScope is a local network discovery and device monitoring web application running on Windows 11. It provides active interface introspection, Scapy-based ARP subnet scanning, IEEE MAC OUI manufacturer resolution, reverse DNS hostnames, user device nicknames, SQLite historical persistence with WAL mode, and a responsive dark-themed dashboard.

---

## 2. Core Runtime & Language
- **Language**: Python 3.11+ (Primary development & verified environment: Python 3.14.6 AMD64 on Windows 11).
- **Type Annotations**: Strict PEP 484 / PEP 563 / PEP 604 type annotations across all operational modules with `from __future__ import annotations`.
- **Runtime Execution**: Synchronous and multi-threaded execution utilizing Python standard library daemon threads and re-entrant mutex locks.
- **Launchers**:
  - `run.py`: Production preflight diagnostic launcher checking Python runtime, dependencies, Npcap drivers, and database initialization.
  - `run.bat`: Windows batch runner for double-click startup.

---

## 3. Web Framework & HTTP Services
- **Flask** (`flask>=3.1.0`): WSGI application factory (`app.py:create_app`) serving the dashboard single-page application and modular JSON REST API Blueprint (`api/routes.py`).
- **Flask-CORS** (`flask-cors>=5.0.0`): Cross-Origin Resource Sharing enabled for local and API communication.
- **Werkzeug** (`werkzeug>=3.1.0`): Underlying WSGI request dispatcher and HTTP exception handling.
- **Jinja2** (`jinja2>=3.1.0`): Server-side templating engine for rendering `templates/index.html`.

---

## 4. Networking & System Introspection
- **Scapy** (`scapy>=2.6.0`):
  - Layer 2 raw packet crafting and network scanning engine (`scanner/discovery.py`).
  - Constructs `Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=cidr)` broadcast frames and transmits via `srp()`.
- **Npcap Driver** (Windows):
  - Kernel-level packet capture driver in WinPcap API-compatible mode providing raw Ethernet frame injection on Windows 11.
- **psutil** (`psutil>=6.1.0`):
  - Inspects network adapter statistics (`net_if_stats()`) and IP bindings (`net_if_addrs()`).
  - Classifies interfaces (`WIFI`, `ETHERNET`, `LOOPBACK`, `VIRTUAL`, `UNKNOWN`) and selects optimal default physical interface.
- **ipaddress** (Python Standard Library):
  - Subnet CIDR calculation and defensive CIDR validation.
- **Windows System Routing (`route.exe`)**:
  - Subprocess execution of `route print 0.0.0.0` parsing the active default gateway IP.
- **IEEE OUI & MAC Engine** (`scanner/oui.py`):
  - Curated offline database of IEEE 24-bit OUI prefixes.
  - Detects IEEE 802 Locally Administered Addresses (LAA) identifying private randomized MACs (iOS 14+, Android 10+).
- **Socket & DNS** (`scanner/hostname.py`):
  - Thread-bounded `socket.gethostbyaddr` reverse DNS lookups with timeout guards.

---

## 5. Persistence & Database
- **SQLite 3** (`database/db.py`, `database/models.py`):
  - Embedded zero-configuration SQL database (`netscope.db`).
  - **WAL Mode**: `PRAGMA journal_mode = WAL;` enables non-blocking concurrent reads during active background scan writes.
  - **Foreign Key Integrity**: `PRAGMA foreign_keys = ON;` with cascading deletions.
  - **Data Models**:
    - `devices`: Unique hardware tracking with MAC, IP, hostname, custom nickname, manufacturer, first_seen, last_seen, and status.
    - `scan_history`: Audit trail of executed scan sessions (duration, count, status, error).
    - `scan_results`: Relational join table linking scan sessions to observed devices.

---

## 6. Frontend Stack
- **HTML5**: Accessible, semantic dashboard layout (`templates/index.html`) featuring network configuration overview cards, scan trigger toolbar, live status indicators, searchable inventory table, and historical audit log modal.
- **CSS3**: Modern responsive stylesheet (`static/css/style.css`) with CSS Custom Properties (variables), dark-mode utility aesthetic, Flexbox, CSS Grid, and monospace tabular data typography.
- **Vanilla JavaScript (ES6+)**: Pure client-side controller (`static/js/app.js`) with zero external frameworks or node/npm build dependencies. Handles asynchronous API polling (`fetch`), real-time substring search filtering, and inline device renaming.

---

## 7. Testing & Quality Assurance
- **pytest** (`pytest>=9.0.0`): Unit, integration, and resilience test runner (130 automated tests passing 100%).
- **pytest-cov** (`pytest-cov>=6.0.0`): Test coverage reporting (94% coverage across operational modules).
- **unittest.mock**: Hermetic mocking of Scapy raw sockets, network drivers, and operating system exceptions.
