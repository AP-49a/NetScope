# NetScope — Codebase Structure

## 1. Directory Tree

```
netscope/
├── .env.example             # Template for local environment configuration
├── .gitignore               # Ignored files (venv, logs, databases, cache)
├── app.py                   # Flask application factory and WSGI entry point
├── config.py                # Centralized environment-based settings and constants
├── plan.md                  # Project Implementation Plan (7 phases)
├── README.md                # Comprehensive product and user documentation
├── requirements.txt         # Pinned production dependencies
├── run.bat                  # Windows 11 batch launcher
├── run.py                   # Self-contained preflight diagnostic launcher
│
├── .planning/               # GSD project tracking & planning directory
│   ├── ROADMAP.md           # Master roadmap tracking all 7 phases
│   ├── STATE.md             # Active project state and milestone tracking
│   ├── codebase/            # Codebase mapping documents (7 architecture files)
│   └── phases/              # Detailed phase plans, research, and verifications
│
├── api/                     # REST API Blueprint and route controllers
│   ├── __init__.py
│   └── routes.py            # Endpoints: /api/network, /api/scan, /api/devices, etc.
│
├── database/                # SQLite connection pool and data access models
│   ├── __init__.py
│   ├── db.py                # Schema migration, WAL mode, connection context manager
│   └── models.py            # Device upsert, offline transitions, scan session audit
│
├── docs/                    # Technical documentation
│   ├── api.md               # Complete REST API specification
│   ├── architecture.md      # Detailed system architecture reference
│   └── development-roadmap.md # Implementation roadmap archive
│
├── logs/                    # Runtime application logs
│   └── netscope.log         # Rotating log file (5 MB, 3 backups)
│
├── scanner/                 # Network discovery and introspection engine
│   ├── __init__.py
│   ├── discovery.py         # Scapy ARP packet broadcast engine & data models
│   ├── hostname.py          # Reverse DNS lookup with thread timeout bounds
│   ├── interface.py         # psutil network interface discovery & classification
│   ├── network.py           # CIDR calculations & Windows default gateway parsing
│   └── oui.py               # IEEE MAC OUI database & private randomized MAC detection
│
├── services/                # Business logic & background service coordinators
│   ├── __init__.py
│   └── scan_service.py      # Thread-safe scan state machine & daemon thread worker
│
├── static/                  # Frontend static assets
│   ├── css/
│   │   └── style.css        # Responsive dark-theme dashboard styles
│   └── js/
│       └── app.js           # Client-side controller (polling, search filter, rename)
│
├── templates/               # Server-rendered HTML templates
│   └── index.html           # Main dashboard template
│
├── tests/                   # Automated test suite (130 tests passing)
│   ├── conftest.py          # Pytest fixtures and log redirection
│   ├── test_api.py          # Flask route and REST endpoint tests
│   ├── test_database.py     # SQLite persistence, schema, and device lifecycle tests
│   ├── test_discovery.py    # Scapy ARP, OUI lookup, and hostname resolution tests
│   ├── test_frontend.py     # Frontend HTML/CSS/JS contract verification tests
│   ├── test_integration.py  # End-to-end multi-scan lifecycle tests
│   ├── test_interface.py    # psutil interface classification tests
│   ├── test_network.py      # Subnet CIDR and gateway parsing tests
│   └── test_resilience.py   # Fault tolerance, stress, and input validation tests
│
└── utils/                   # Shared utility modules
    ├── __init__.py
    └── logger.py            # Dual-stream logging with file rotation and fallbacks
```

---

## 2. Module Responsibilities & Lines of Code

| Module | Primary Responsibility | Key Classes / Functions |
|---|---|---|
| `app.py` | Application factory | `create_app()` |
| `config.py` | Typed settings | `Config`, `DATABASE_PATH`, `SCAN_TIMEOUT`, `LOG_LEVEL` |
| `run.py` | Preflight launcher | `check_python_version()`, `check_dependencies()`, `is_admin()`, `main()` |
| `api/routes.py` | API routing | `get_network()`, `start_scan()`, `get_status()`, `get_devices()`, `update_device_name()`, `get_history()` |
| `database/db.py` | Connection & schema | `get_db_connection()`, `init_db()` |
| `database/models.py` | Data access | `upsert_device()`, `set_device_custom_name()`, `mark_unseen_devices_offline()`, `record_scan_session()`, `get_all_devices()` |
| `scanner/interface.py`| Interface classification | `InterfaceInfo`, `InterfaceKind`, `list_active_interfaces()`, `get_preferred_interface()` |
| `scanner/network.py` | Network calculation | `NetworkConfig`, `calculate_cidr()`, `get_default_gateway()`, `get_network_config()` |
| `scanner/discovery.py`| ARP packet engine | `DiscoveredDevice`, `ScanResult`, `scan_network()` |
| `scanner/oui.py` | Hardware vendor lookup | `get_manufacturer()`, `is_locally_administered()`, `normalize_mac_prefix()` |
| `scanner/hostname.py` | Reverse DNS | `resolve_hostname()` |
| `services/scan_service.py`| Concurrency & state | `ScanService`, `ScanState`, `start_scan()`, `_run_scan_worker()`, `get_status()` |
| `utils/logger.py` | Logging utility | `get_logger()` |
