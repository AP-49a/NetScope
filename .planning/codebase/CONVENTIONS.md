# NetScope — Coding Conventions & Standards

## 1. Code Style & Language Standards

- **Python Version**: Target Python 3.11+ (verified on Python 3.14.6).
- **PEP 8 Compliance**: 4-space indentation, 100-character line length ceiling for readability, standard naming conventions (lowercase with underscores for functions/variables, PascalCase for classes, UPPER_CASE for constants).
- **Type Annotations**:
  - All public functions, methods, and classes must use strict type annotations (`typing` and Python 3.10+ union syntax `|`).
  - Every module starts with `from __future__ import annotations`.
- **Filesystem Paths**:
  - Always use `pathlib.Path` objects instead of raw string concatenations or `os.path`.

---

## 2. Architecture & Design Patterns

### 2.1 Factory Pattern
- Flask application is instantiated via factory function `create_app(test_config=None)` in `app.py`.
- Enables hermetic test configuration injection (`TESTING=True`, isolated temporary databases).

### 2.2 Singleton State Management
- `ScanService` is implemented as a singleton (`scan_service = ScanService()`) in `services/scan_service.py`.
- All operational state transitions are thread-safe and governed by a mutual exclusion lock (`self._lock = threading.Lock()`).

### 2.3 Context Managers for Resources
- SQLite connections are managed strictly through `@contextmanager def get_db_connection(db_path=None)`.
- Enforces automatic `commit()` on block exit and automatic `rollback()` on exceptions.

---

## 3. Error Handling & Defensive Programming

### 3.1 Non-Crashing Resilience
- Network operations (hardware disconnections, raw socket permissions) must never crash the Flask server process.
- Errors are captured, logged, recorded in scan history, and communicated back through HTTP response codes (`400 Bad Request`, `404 Not Found`, `409 Conflict`, `500 Internal Server Error`).

### 3.2 Defensive Input Validation
- All external inputs (e.g. CIDR strings in `POST /api/scan`) are validated defensively using standard library parsers (`ipaddress.ip_network(cidr, strict=False)`).
- Malformed inputs immediately return HTTP 400 with a descriptive JSON error payload.

### 3.3 Honest Data Reporting
- Never invent placeholder hostnames or manufacturers. If an attribute cannot be resolved, return `None` (rendered in UI as `Unresolved` or `Unknown`).
- If an IEEE 802 Locally Administered Address (LAA) is detected, explicitly report it as a `Private MAC (Mobile/PC)`.

---

## 4. Concurrency & Thread-Safety Rules

1. **Single-Writer Lock**: Only one active ARP scan can be performed at any time.
2. **Daemon Worker Threads**: Scans must run in a background daemon thread (`threading.Thread(target=..., daemon=True)`).
3. **Database Concurrency**: Rely on SQLite Write-Ahead Logging (`WAL`) to prevent database lock contention between background writes and foreground HTTP reads.
