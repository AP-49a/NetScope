# Phase 3 Research: Backend and REST API Development

## 1. Domain & Framework Realities (Flask 3.x)

### 1.1 Flask Application Factory Pattern
- Implementing `create_app(config_override=None) -> Flask` in `app.py` allows:
  - Clean separation between production server entry point (`python app.py`) and test runner.
  - Test isolation: test suites can instantiate fresh app instances with custom settings (e.g. testing mode, mock services).
- Blueprint modularity:
  - `api/routes.py` encapsulates all `/api/...` endpoints within `api_bp = Blueprint("api", __name__, url_prefix="/api")`.
  - Frontend root route (`/`) serves the static template from `templates/index.html`.

### 1.2 Non-Blocking Scan Orchestration & Concurrency Control
- **Problem**: An ARP scan over a `/24` network takes 1-3 seconds. In a single-threaded WSGI server, running `scan_network()` synchronously inside an HTTP request handler blocks the entire server, preventing status polling or other requests from completing.
- **Solution (`services/scan_service.py`)**:
  - Encapsulate scan state in a thread-safe singleton or service instance.
  - Maintain an internal `threading.Lock()` to guard state transitions.
  - When `POST /api/scan` is received:
    - Attempt to acquire the lock without blocking (`lock.acquire(blocking=False)`).
    - If already acquired, return `409 Conflict` (`{"error": "A scan is already in progress.", "status": "scanning"}`).
    - If free, set state to `"scanning"` and launch the scan task inside a background daemon thread (`threading.Thread(target=..., daemon=True)`).
    - The worker thread invokes `scanner.discovery.scan_network()`, updates the device cache and execution metrics upon completion or error, transitions status to `"completed"` (or `"error"`), and releases the lock.
  - State tracking:
    - `state`: `"idle"` | `"scanning"` | `"completed"` | `"error"`
    - `last_scan`: metadata dictionary (started, completed, duration, device count)
    - `devices`: cached list of `DiscoveredDevice` dictionaries.

### 1.3 REST API Endpoints Specification
- **`GET /api/network`**:
  - Invokes `get_network_config()`.
  - Returns `200 OK` with JSON object:
    ```json
    {
      "interface_name": "Wi-Fi",
      "ip_address": "192.168.1.15",
      "subnet_mask": "255.255.255.0",
      "gateway": "192.168.1.1",
      "cidr": "192.168.1.0/24",
      "prefix_length": 24,
      "is_complete": true
    }
    ```
- **`POST /api/scan`**:
  - Accepts optional JSON body `{"cidr": "...", "interface": "...", "timeout": 2.0}`.
  - Triggers background scan via `ScanService`.
  - Returns `202 Accepted` with:
    ```json
    {
      "message": "Scan initiated",
      "status": "scanning",
      "target_cidr": "192.168.1.0/24"
    }
    ```
  - Returns `409 Conflict` if a scan is already running.
- **`GET /api/status`**:
  - Returns current scan status and last run metadata:
    ```json
    {
      "status": "idle" | "scanning" | "completed" | "error",
      "is_scanning": false,
      "last_scan": {
        "started_at": "...",
        "completed_at": "...",
        "duration_seconds": 1.25,
        "device_count": 4,
        "error_message": null
      }
    }
    ```
- **`GET /api/devices`**:
  - Returns collection of discovered devices from the latest scan:
    ```json
    {
      "count": 2,
      "devices": [
        {
          "ip_address": "192.168.1.1",
          "mac_address": "00:00:0C:11:22:33",
          "hostname": "gateway.local",
          "manufacturer": "Cisco",
          "status": "online"
        }
      ]
    }
    ```

### 1.4 Testing Strategy with Flask Test Client
- Use `app.test_client()` for in-process HTTP integration testing without spawning live sockets.
- Mock `ScanService` or `scanner.discovery.scan_network` to test synchronous and asynchronous transitions deterministically.
- Verify status codes (200, 202, 400, 409), JSON structure, and error envelopes.
