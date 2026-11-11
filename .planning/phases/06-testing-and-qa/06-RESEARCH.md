# Phase 6 Research: Testing and Quality Assurance

## 1. Quality Engineering & Vulnerability Analysis

### 1.1 End-to-End Pipeline Cohesion
- A complete network discovery workflow exercises five distinct architectural layers:
  ```
  HTTP Client -> Flask Route (api/routes.py) -> Service Coordinator (services/scan_service.py)
              -> Engine (scanner/discovery.py) -> Persistence (database/models.py) -> SQLite Store
  ```
- To verify system resilience, integration tests must confirm that:
  1. An asynchronous scan job writes to the database without race conditions.
  2. Data fetched via subsequent `GET /api/devices` accurately reflects the SQLite state.
  3. Subsequent scans appropriately mark unobserved devices as `offline` without wiping historical records.
  4. Server and engine recover seamlessly after simulated hardware / driver exceptions.

### 1.2 Failure Modes & Resilience Scenarios

#### Scenario A: Adapter Disconnection Mid-Scan
- If an adapter goes down during `srp()`, Scapy or the OS raises `OSError` (e.g., `Network is unreachable`).
- **Required Behavior**: `ScanService` must capture the exception, set `state = ERROR`, record the failure in `scan_history`, release the concurrency lock, and remain ready to accept future scan requests when connectivity returns.

#### Scenario B: Consecutive Rapid Scan Submissions (Race Conditions)
- If multiple HTTP clients concurrently submit `POST /api/scan`, exactly one client must receive `202 Accepted` while all others immediately receive `409 Conflict`.
- Once the active scan completes, the lock must be cleanly freed so the next scan is accepted without server restart.

#### Scenario C: High Host Density (Subnet Stress)
- A full `/24` subnet scan can yield up to 254 responding devices.
- Serialization, database batch upserts, and JSON rendering must execute in under 100ms without memory bloat or CPU spikes.

#### Scenario D: Corrupted / Malformed Network Inputs
- The API must reject out-of-spec parameters defensively:
  - Malformed CIDR targets (e.g. `999.999.999.999/24`, `abc/xyz`, empty strings).
  - Malformed timeouts (e.g. `-5`, `0`, non-numeric strings).

---

## 2. Test Execution & Coverage Targets
- Goal: Maintain 100% pass rate across the entire test suite.
- Coverage Target: ≥90% line coverage across all operational packages (`scanner`, `services`, `database`, `api`, `utils`).
- Execution Time: Under 5 seconds for the entire automated suite to preserve fast developer iteration loops.
