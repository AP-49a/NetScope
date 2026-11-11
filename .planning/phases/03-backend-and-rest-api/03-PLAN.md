# Phase 3 Plan: Backend and REST API Development

## Phase Objective
Connect the Phase 1 network configuration detection and Phase 2 ARP scanning engine to a Flask application, exposing standardized REST API endpoints (`/api/network`, `/api/scan`, `/api/devices`, `/api/status`) with non-blocking background scan coordination, concurrency locking, and automated API tests.

**Phase Directory:** `.planning/phases/03-backend-and-rest-api`  
**Status:** **Ready for Execution**  

---

## 1. Architectural Scope & Guardrails

```
┌─────────────────────────────────────────────────────────────┐
│                       In Scope (Phase 3)                    │
├─────────────────────────────────────────────────────────────┤
│ • Flask application factory in app.py (create_app)          │
│ • services/scan_service.py with thread safety & locks       │
│ • Background daemon thread runner for non-blocking scans    │
│ • api/routes.py implementing GET /network, POST /scan,      │
│   GET /devices, GET /status                                 │
│ • Error envelopes & HTTP status codes (200, 202, 400, 409)  │
│ • Integration test suite using test_client (test_api.py)    │
│ • Serving index.html on root route (/)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Locked Out (Phase 4+)                    │
├─────────────────────────────────────────────────────────────┤
│ ✕ Interactive frontend JavaScript dashboard logic (Phase 4) │
│ ✕ SQLite database persistence (Phase 5)                     │
│ ✕ Device historical tracking across server restarts (Phase 5│
└─────────────────────────────────────────────────────────────┘
```

---

## 2. API Contract Specification

| Method | Route | Description | Success Code | Conflict / Error Code |
|---|---|---|:---:|:---:|
| `GET` | `/api/network` | Returns active adapter name, IP, mask, gateway, CIDR | `200 OK` | `500 Internal Error` |
| `POST` | `/api/scan` | Triggers background scan (optional custom CIDR) | `202 Accepted` | `409 Conflict`, `400 Bad Request` |
| `GET` | `/api/status` | Returns current scan state (`idle`, `scanning`, `completed`, `error`) and metrics | `200 OK` | — |
| `GET` | `/api/devices` | Returns cached list of discovered devices from latest scan | `200 OK` | — |
| `GET` | `/` | Serves dashboard HTML template (`index.html`) | `200 OK` | — |

---

## 3. Work Breakdown & Task Decomposition

### Wave 1: Service Layer & Scan Orchestration
* **Task 3.1: Implement Scan Orchestrator Service**
  * **File:** `services/scan_service.py`, `services/__init__.py`
  * **Responsibility**:
    * Thread-safe scan manager class `ScanService`.
    * Track scan state enum/string: `"idle"`, `"scanning"`, `"completed"`, `"error"`.
    * Enforce `threading.Lock` to prevent concurrent scans (non-blocking acquire; returns false if busy).
    * Launch background daemon thread executing `scanner.discovery.scan_network`.
    * Store latest `ScanResult` and list of `DiscoveredDevice` objects in-memory.
    * Provide getter methods: `get_status()`, `get_devices()`, `start_scan(cidr=None, timeout=None)`.
  * **Verification**: Unit tests testing state transitions and simultaneous start rejections.

### Wave 2: REST API & Application Factory
* **Task 3.2: Implement Flask API Blueprint**
  * **File:** `api/routes.py`
  * **Responsibility**:
    * Register Blueprint `api_bp = Blueprint("api", __name__, url_prefix="/api")`.
    * Implement `GET /api/network` returning `get_network_config()` as JSON.
    * Implement `POST /api/scan` checking for in-progress scans (returns 409 if busy, 202 if started).
    * Implement `GET /api/status` returning current operational state.
    * Implement `GET /api/devices` returning formatted list of devices.
    * Validate request payloads defensively (e.g. invalid CIDR formats).
  * **Verification**: Route handlers return clean JSON envelopes with correct headers.

* **Task 3.3: Complete Flask Application Factory**
  * **File:** `app.py`
  * **Responsibility**:
    * Implement `create_app(config_override=None) -> Flask`.
    * Configure CORS, logging, and templates folder.
    * Register `api_bp` Blueprint and root view (`GET /`) rendering `templates/index.html`.
    * Provide entry point `if __name__ == "__main__": app.run(...)`.
  * **Verification**: App instantiates and serves `/` and `/api/status`.

### Wave 3: Testing & Verification
* **Task 3.4: Automated API Integration Tests**
  * **File:** `tests/test_api.py`
  * **Responsibility**:
    * Test all endpoints using `app.test_client()`.
    * Test `GET /api/network` returns valid network config.
    * Test `POST /api/scan` initiates scan and returns 202.
    * Test concurrent `POST /api/scan` returns 409 Conflict.
    * Test `GET /api/status` reflects state changes.
    * Test `GET /api/devices` returns discovered devices.
    * Test root `/` returns 200 and loads `index.html`.
  * **Verification**: `python -m pytest tests/test_api.py -v` passes 100%.

* **Task 3.5: Project Roadmap & Documentation Updates**
  * **Files:** `README.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`
  * **Responsibility**: Update project state, document API endpoints with examples.

---

## 4. Acceptance Criteria Checklist

- [ ] Flask application factory initializes cleanly via `create_app()`.
- [ ] `GET /api/network` returns active network configuration.
- [ ] `POST /api/scan` starts an asynchronous background scan without blocking the web server.
- [ ] Subsequent scan requests while a scan is active return HTTP 409 Conflict.
- [ ] `GET /api/status` accurately reports current state (`idle`, `scanning`, `completed`, `error`).
- [ ] `GET /api/devices` returns array of discovered devices.
- [ ] Scanner errors do not crash the Flask server process.
- [ ] All new tests in `tests/test_api.py` pass.
- [ ] All 89 existing Phase 1 & 2 tests continue to pass without regression.
