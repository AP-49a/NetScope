# Phase 5 Plan: Database and Device History

## Phase Objective
Implement an embedded SQLite persistence layer to store discovered device records, maintain device lifecycle (`first_seen` and `last_seen` timestamps, online/offline status transitions), record historical scan sessions, and ensure data persists across server restarts.

**Phase Directory:** `.planning/phases/05-database-and-history`  
**Status:** **Ready for Execution**  

---

## 1. Architectural Scope & Guardrails

```
┌─────────────────────────────────────────────────────────────┐
│                       In Scope (Phase 5)                    │
├─────────────────────────────────────────────────────────────┤
│ • database/db.py: connection manager with WAL & foreign keys│
│ • Database initialization & schema migrations (init_db)     │
│ • database/models.py: upsert device, preserve first_seen,   │
│   update last_seen, mark missing devices offline            │
│ • scan_history and scan_results audit table persistence     │
│ • Integration with ScanService: auto-save scan results      │
│ • Update GET /api/devices to return persistent inventory    │
│ • Update GET /api/history (or scan sessions endpoint)       │
│ • Automated database test suite (tests/test_database.py)    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Locked Out (Phase 6+)                    │
├─────────────────────────────────────────────────────────────┤
│ • End-to-end multi-adapter regression testing (Phase 6)     │
│ • Packaging and release distribution hardening (Phase 7)    │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Database Schema Specification

```sql
-- Devices table
CREATE TABLE IF NOT EXISTS devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mac_address TEXT NOT NULL UNIQUE,
    ip_address TEXT NOT NULL,
    hostname TEXT,
    manufacturer TEXT,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'online'
);

CREATE INDEX IF NOT EXISTS idx_devices_mac ON devices(mac_address);
CREATE INDEX IF NOT EXISTS idx_devices_ip ON devices(ip_address);

-- Scan sessions audit table
CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cidr TEXT NOT NULL,
    interface_name TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    device_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_scan_history_started ON scan_history(started_at);

-- Scan-to-device join records
CREATE TABLE IF NOT EXISTS scan_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL,
    device_id INTEGER NOT NULL,
    FOREIGN KEY (scan_id) REFERENCES scan_history(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
);
```

---

## 3. Work Breakdown & Task Decomposition

### Wave 1: Database Foundation & Schema
* **Task 5.1: SQLite Connection & Schema Management**
  * **File:** `database/db.py`
  * **Responsibility**:
    * Context-managed connection factory `get_db_connection(db_path=None)`.
    * Enforce `PRAGMA foreign_keys = ON;`, `PRAGMA journal_mode = WAL;`, `row_factory = sqlite3.Row`.
    * Function `init_db(db_path=None)` to create tables and indexes idempotently.
  * **Verification**: In-memory connection test verifying schema initialization.

### Wave 2: Data Access Models & Persistence Operations
* **Task 5.2: Device & Scan Models**
  * **File:** `database/models.py`
  * **Responsibility**:
    * `upsert_device(mac, ip, hostname=None, manufacturer=None, timestamp=None, db_path=None) -> int`:
      - Inserts new record if MAC is unseen (setting `first_seen` = `last_seen` = `timestamp`).
      - Updates `ip`, `last_seen`, and status to `'online'` if MAC already exists, strictly preserving `first_seen`.
      - Preserves existing hostname/manufacturer if newly scanned value is null.
    * `mark_unseen_devices_offline(active_macs: list[str], db_path=None) -> int`:
      - Transitions all devices whose MAC is not in `active_macs` to `status = 'offline'`.
    * `record_scan_session(scan_result: ScanResult, db_path=None) -> int`:
      - Records scan metadata in `scan_history` and links associated devices in `scan_results`.
    * `get_all_devices(status_filter=None, db_path=None) -> list[dict]`:
      - Queries device inventory sorted by `last_seen DESC`.
    * `get_scan_history(limit=20, db_path=None) -> list[dict]`:
      - Queries scan sessions sorted by `started_at DESC`.
  * **Verification**: Unit tests verifying `first_seen` persistence across updates and offline transitions.

### Wave 3: Service Integration & API Wiring
* **Task 5.3: ScanService & API Endpoint Integration**
  * **Files:** `services/scan_service.py`, `api/routes.py`
  * **Responsibility**:
    * Initialize DB on `create_app()` / `ScanService.__init__()`.
    * In `ScanService._run_scan_worker()`:
      - Call `upsert_device()` for each replying device.
      - Call `mark_unseen_devices_offline()` for non-replying devices.
      - Call `record_scan_session()`.
    * Update `GET /api/devices`: return all devices from persistent database.
    * Add `GET /api/history`: return recent scan history records.
  * **Verification**: Server restarts retain discovered devices in API response.

### Wave 4: Testing & Verification
* **Task 5.4: Automated Database Tests**
  * **File:** `tests/test_database.py`
  * **Responsibility**:
    * Test database initialization on isolated temp/in-memory databases.
    * Test first-time device insertion.
    * Test device re-discovery (verifying `first_seen` remains unchanged and `last_seen` updates).
    * Test marking missing devices as offline.
    * Test scan history recording and foreign key relationships.
    * Test retrieving devices with status filters.
  * **Verification**: `python -m pytest tests/test_database.py -v` passes 100%.

* **Task 5.5: Roadmap & State Updates**
  * **Files:** `README.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`
  * **Responsibility**: Update project state and milestone documentation.

---

## 4. Acceptance Criteria Checklist

- [ ] SQLite database initializes cleanly with WAL mode and foreign key enforcement.
- [ ] New devices are inserted with identical `first_seen` and `last_seen` timestamps.
- [ ] Re-discovered devices update their `last_seen` timestamp while preserving original `first_seen`.
- [ ] Previously discovered devices that do not respond transition to `status = 'offline'` without deletion.
- [ ] Scan history records scan duration, CIDR, adapter, device count, and completion state.
- [ ] Discovered devices persist across Flask server restarts.
- [ ] `GET /api/devices` returns persistent device history.
- [ ] All new tests in `tests/test_database.py` pass.
- [ ] All 104 existing Phase 1, 2, 3, and 4 tests continue to pass without regression.
