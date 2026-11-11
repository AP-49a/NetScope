# NetScope — Technology Stack

## 1. Overview
NetScope is a local network discovery and monitoring web application designed to run on Windows 11. It provides active interface introspection, network configuration detection, and is structured for future ARP-based active device scanning and web UI presentation.

## 2. Core Runtime & Language
- **Language**: Python 3.11+ (Primary development & testing environment: Python 3.14.6 AMD64 on Windows 11).
- **Type Annotations**: Strict PEP 484 / PEP 563 / PEP 604 type annotations across all modules with `from __future__ import annotations`.
- **Runtime Model**: Synchronous standard library execution with system subprocess calls and OS API bindings.

## 3. Web Framework & HTTP Services
- **Flask** (`flask==3.1.3`): WSGI web framework reserved for serving backend REST APIs and frontend templates (Phase 2+).
- **Flask-CORS** (`flask-cors==6.0.5`): Cross-Origin Resource Sharing handling for development and external client calls.
- **Werkzeug** (`werkzeug==3.1.9`): Underlying WSGI utility library and HTTP request handler.
- **Jinja2** (`jinja2==3.1.6`): Server-side templating engine for rendering initial HTML views (`templates/index.html`).

## 4. Networking & System Introspection
- **psutil** (`psutil==7.2.2`):
  - Cross-platform process and system monitoring library.
  - Used in `scanner/interface.py` via `psutil.net_if_stats()` and `psutil.net_if_addrs()` to enumerate interfaces, link state (UP/DOWN), MAC addresses, and assigned IP configurations without requiring administrative privileges.
- **ipaddress** (Standard Library):
  - Dotted-decimal netmask calculation and CIDR generation (`calculate_cidr`, `netmask_to_prefix_length`).
- **Windows System Utilities**:
  - `route.exe` via `subprocess.run(["route", "print", "0.0.0.0"])` for default gateway determination from the Windows IPv4 active routing table.
- **Scapy** (`scapy==2.8.0`):
  - Packet crafting and decoding library.
  - Installed and reserved for Phase 2 ARP-based active local host discovery.
  - Requires Npcap on Windows for raw socket operations.

## 5. Configuration & Environment Management
- **python-dotenv** (`python-dotenv==1.2.4`):
  - Loads configuration variables from `.env` files into `os.environ` via `dotenv.load_dotenv(BASE_DIR / ".env")`.
- **pathlib** (Standard Library):
  - Filesystem path manipulations (`Path(__file__).resolve().parent`) ensuring OS-independent path resolution.

## 6. Testing & Quality Assurance
- **pytest** (`pytest==9.2.0`):
  - Test runner and test fixture management framework.
- **pytest-cov** (`pytest-cov==7.1.0`):
  - Code coverage reporting integration.
- **unittest.mock** (Standard Library):
  - Comprehensive mocking for OS interfaces (`psutil`, `subprocess.run`, `socket`, `open`).

## 7. Frontend Stack (Planned / Staged)
- **HTML5 / CSS3**: Vanilla, responsive styles with CSS variables and flexbox layout (`static/css/style.css`, `templates/index.html`).
- **JavaScript**: Native ECMAScript (Vanilla JS, `static/js/app.js`), no heavy build chains or bundlers required.

## 8. Persistence Stack (Planned)
- **SQLite3** (Standard Library):
  - Embedded relational database (`database/db.py`, `database/models.py`) planned for Phase 2+ to record scan sessions, device discovery history, and status changes.
