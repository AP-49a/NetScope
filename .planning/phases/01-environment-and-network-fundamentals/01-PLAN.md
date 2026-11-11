# Phase 1 Plan: Environment Setup & Network Fundamentals

## Phase Objective
Establish a clean, tested Python 3.11+ development environment, modular project architecture, centralized logging, and reliable Windows 11 network introspection without introducing premature Phase 2 scanning features.

---

## 1. Context & Scope Fence

- **In Scope**:
  - Virtual environment configuration and dependency management (`requirements.txt`).
  - Directory structure scaffolding matching the system architecture.
  - Centralized application logging (`utils/logger.py`) with stdout and rotating file handler.
  - Active adapter introspection (`scanner/interface.py`) distinguishing Ethernet, Wi-Fi, virtual, and loopback adapters.
  - IP, netmask, default gateway detection, and CIDR range calculation (`scanner/network.py`).
  - Hermetic unit tests with mocked system calls (`tests/test_interface.py`, `tests/test_network.py`).
  - Documentation and Npcap requirements guide (`README.md`, `docs/architecture.md`, `docs/development-roadmap.md`).

- **Out of Scope (Locked for Future Phases)**:
  - Scapy ARP packet transmission (Phase 2).
  - Flask endpoints or web server execution (Phase 3).
  - Web dashboard UI rendering (Phase 4).
  - SQLite database schemas or persistence (Phase 5).

---

## 2. Tasks & Execution Sequence

### Task 1.1: Dependency and Environment Setup
- **Target Files**: `requirements.txt`, `.env.example`, `config.py`, `.gitignore`
- **Actions**:
  - Pin runtime dependencies (`flask`, `flask-cors`, `psutil`, `scapy`, `python-dotenv`) and test dependencies (`pytest`, `pytest-cov`).
  - Configure `.env.example` with host, port, logging level, and preferred interface settings.
  - Implement `config.py` using `pathlib.Path` and `python-dotenv` for typed settings.
- **Verification**: `python -c "import flask, psutil, scapy, dotenv; print('OK')"` exits with code 0.

### Task 1.2: Centralized Logging Utility
- **Target Files**: `utils/logger.py`, `logs/.gitkeep`
- **Actions**:
  - Implement `get_logger(__name__)` and `configure_logging()`.
  - Attach `StreamHandler` for console output and `RotatingFileHandler` for `logs/netscope.log`.
  - Add defensive exception handling for unwritable log paths (graceful fallback to console).
- **Verification**: Ensure loggers emit structured log lines with format `%(asctime)s | %(levelname)-8s | %(name)s | %(message)s`.

### Task 1.3: Network Interface Enumeration & Classification
- **Target Files**: `scanner/interface.py`
- **Actions**:
  - Define `InterfaceKind` enum (`LOOPBACK`, `ETHERNET`, `WIFI`, `VIRTUAL`, `UNKNOWN`).
  - Define `InterfaceInfo` dataclass holding name, kind, status, IPv4, netmask, MAC, and flags.
  - Implement `list_interfaces()` and `list_active_interfaces()` using `psutil`.
  - Implement `get_preferred_interface(preferred_name)` with priority fallback (preferred -> Ethernet -> Wi-Fi -> non-virtual).
- **Verification**: Unit tests verifying classification of virtual, Wi-Fi, Ethernet, and loopback adapters.

### Task 1.4: Network Configuration & CIDR Calculation
- **Target Files**: `scanner/network.py`
- **Actions**:
  - Define `NetworkConfig` dataclass and `is_complete` property.
  - Implement `netmask_to_prefix_length(netmask)` using `ipaddress`.
  - Implement `calculate_cidr(ip_address, netmask)` stripping host bits.
  - Implement `get_default_gateway()` parsing `route print 0.0.0.0` output via regex.
  - Implement `get_network_config()` and `get_all_network_configs()`.
- **Verification**: Unit tests covering valid and malformed IPs/masks, zeroed host bits, and multi-interface scenarios.

### Task 1.5: Unit Test Suite & QA
- **Target Files**: `tests/conftest.py`, `tests/test_interface.py`, `tests/test_network.py`
- **Actions**:
  - Implement session fixture in `conftest.py` redirecting logs to a temporary directory.
  - Write parametrized tests for CIDR calculation and mask conversion.
  - Mock `psutil.net_if_stats`, `psutil.net_if_addrs`, and `subprocess.run`.
- **Verification**: `python -m pytest tests/ -v` passes 100%.

### Task 1.6: Stubs and Architecture Scaffolding
- **Target Files**: `scanner/discovery.py`, `api/routes.py`, `database/db.py`, `database/models.py`, `app.py`, `templates/index.html`, `static/css/style.css`, `static/js/app.js`
- **Actions**:
  - Create non-functional stubs for Phase 2-5 modules with explanatory docstrings.
  - Ensure zero circular dependencies across packages.
- **Verification**: All modules import cleanly without execution errors.

---

## 3. Acceptance Verification Checklist

- [x] Environment configured with Python 3.11+ and pinned `requirements.txt`.
- [x] `psutil`, `flask`, `scapy`, and `dotenv` import successfully.
- [x] Interface enumeration correctly classifies active vs inactive adapters.
- [x] Local IP, subnet mask, default gateway, and CIDR correctly determined.
- [x] Unavailable adapters and missing network info handled gracefully without uncaught exceptions.
- [x] Logging system writes to console and file with permission fallback.
- [x] 57 unit tests execute and pass without contacting live networks.
- [x] No Phase 2 scanning logic or full web server prematurely introduced.
