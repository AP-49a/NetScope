# NetScope — Project Structure & File Layout

## 1. Directory Tree

```
NetScope/
│
├── app.py                      # Flask application entry point (Phase 2 stub)
├── config.py                   # Centralized application configuration & environment loader
├── requirements.txt            # Pinned project dependencies
├── .env.example                # Template for environment configuration
├── .gitignore                  # Git exclusions (venv, logs, db, pycache)
├── README.md                   # Installation, setup, quick-start, and documentation
│
├── scanner/                    # Core networking and scanning subsystem
│   ├── __init__.py             # Package marker
│   ├── interface.py            # Network interface enumeration & classification
│   ├── network.py              # IP, subnet mask, gateway, and CIDR calculation
│   └── discovery.py            # ARP-based host discovery engine (Phase 2 stub)
│
├── api/                        # HTTP REST API layer
│   ├── __init__.py             # Package marker
│   └── routes.py               # Flask Blueprint route handlers (Phase 2 stub)
│
├── database/                   # Persistence & relational storage layer
│   ├── __init__.py             # Package marker
│   ├── db.py                   # SQLite connection & schema manager (Phase 2 stub)
│   └── models.py               # SQLite data models & row mappers (Phase 2 stub)
│
├── utils/                      # Shared helper utilities
│   ├── __init__.py             # Package marker
│   └── logger.py               # Centralized dual console/rotating file logger
│
├── templates/                  # Server-side HTML templates
│   └── index.html              # HTML shell for NetScope web dashboard
│
├── static/                     # Frontend static assets
│   ├── css/
│   │   └── style.css           # Modern dark-theme stylesheet
│   ├── js/
│   │   └── app.js              # Frontend UI orchestration script
│   └── assets/                 # Reserved for static images / icons
│
├── tests/                      # Automated test suite
│   ├── __init__.py             # Package marker
│   ├── conftest.py             # pytest session fixtures & temp log redirect
│   ├── test_interface.py       # 28 unit tests for scanner.interface
│   └── test_network.py         # 29 unit tests for scanner.network
│
├── logs/                       # Application logs directory
│   └── .gitkeep                # Retains directory in source control
│
├── docs/                       # Comprehensive documentation
│   ├── architecture.md         # Architecture blueprint & decision records
│   └── development-roadmap.md  # Multi-phase milestone roadmap
│
└── .planning/                  # Project planning & codebase maps
    └── codebase/               # Codebase intelligence & architecture summaries
        ├── STACK.md
        ├── INTEGRATIONS.md
        ├── ARCHITECTURE.md
        ├── STRUCTURE.md
        ├── CONVENTIONS.md
        ├── TESTING.md
        └── CONCERNS.md
```

## 2. Module Responsibilities Matrix

| Module / Path | Phase Status | Primary Responsibility | Primary Dependencies |
|---|---|---|---|
| `config.py` | Complete (Ph 1) | Centralized environment variable management | `dotenv`, `os`, `pathlib` |
| `utils/logger.py` | Complete (Ph 1) | Dual-output logging configuration with fallbacks | `logging`, `logging.handlers`, `sys` |
| `scanner/interface.py` | Complete (Ph 1) | Enumerates adapters, determines state & kind | `psutil`, `socket`, `re`, `dataclasses` |
| `scanner/network.py` | Complete (Ph 1) | Computes CIDR, discovers gateway & masks | `ipaddress`, `subprocess`, `re`, `interface` |
| `scanner/discovery.py` | Stub (Ph 2) | ARP broadcast scanning for live hosts | `scapy` |
| `api/routes.py` | Stub (Ph 2) | REST endpoints for network and device data | `flask`, `scanner` |
| `database/db.py` | Stub (Ph 2) | SQLite database lifecycle management | `sqlite3` |
| `database/models.py` | Stub (Ph 2) | Data models representing scanned devices | `dataclasses` / `sqlite3` |
| `app.py` | Stub (Ph 2) | Web server initialization & Blueprint mounting | `flask`, `config`, `api` |
| `templates/index.html` | Shell (Ph 1) | Web dashboard markup | HTML5 |
| `static/css/style.css` | Shell (Ph 1) | Responsive dashboard styling | CSS3 |
| `static/js/app.js` | Shell (Ph 1) | Dynamic frontend DOM updates | Native ECMAScript |

## 3. Entry Points

- **Phase 1 Inspection Entry Point**:
  ```powershell
  python -c "from scanner.network import get_network_config; print(get_network_config())"
  ```
- **Test Suite Entry Point**:
  ```powershell
  python -m pytest tests/ -v
  ```
- **Phase 2 Application Server Entry Point (Upcoming)**:
  ```powershell
  python app.py
  ```
