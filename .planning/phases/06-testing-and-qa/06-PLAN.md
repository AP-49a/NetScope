# Phase 6 Plan: Testing and Quality Assurance

## Phase Objective
Perform comprehensive quality assurance across all layers of NetScope: build end-to-end integration workflows (API -> Service -> Scanner -> Database), test abnormal failure modes (adapter disconnects, permission constraints, concurrent lock races, high-density host loads), verify non-regression, and establish high test coverage.

**Phase Directory:** `.planning/phases/06-testing-and-qa`  
**Status:** **Ready for Execution**  

---

## 1. Architectural Scope & Guardrails

```
┌─────────────────────────────────────────────────────────────┐
│                       In Scope (Phase 6)                    │
├─────────────────────────────────────────────────────────────┤
│ • End-to-end integration tests (tests/test_integration.py)  │
│ • Failure recovery & resilience tests (test_resilience.py)  │
│ • High-density subnet simulation (250+ host load testing)   │
│ • CIDR input validation hardening in api/routes.py          │
│ • Recovery after simulated driver / network failures        │
│ • Full coverage audit across scanner, services, db, api     │
│ • Verification that all 111 existing tests continue to pass │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Locked Out (Phase 7+)                    │
├─────────────────────────────────────────────────────────────┤
│ • Production release packaging & final branding (Phase 7)   │
│ • Complete user guide & installation manuals (Phase 7)      │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Work Breakdown & Task Decomposition

### Wave 1: Input Validation Hardening
* **Task 6.1: Defensive CIDR & Parameter Validation**
  * **File:** `api/routes.py`
  * **Scope:**
    * In `POST /api/scan`: Validate `cidr` using `ipaddress.ip_network(cidr, strict=False)` if provided.
    * Return `400 Bad Request` with `{"error": "Invalid CIDR network format."}` for malformed targets.
  * **Verification:** Unit tests verifying rejection of malformed CIDRs (`"999.999.999.0/24"`, `"foo"`).

### Wave 2: End-to-End Integration Suite
* **Task 6.2: E2E Pipeline Integration Tests**
  * **File:** `tests/test_integration.py`
  * **Scope:**
    * Exercise full stack: `POST /api/scan` -> `ScanService._run_scan_worker()` -> database insertion -> `GET /api/devices`.
    * Verify multi-scan lifecycle:
      - Scan 1: discovers Host A and Host B (both `online`).
      - Scan 2: discovers Host B and Host C (Host A transitions to `offline`, Host B updates `last_seen` with unchanged `first_seen`, Host C created).
    * Verify `GET /api/history` contains both audit entries.
  * **Verification:** Tests pass with isolated temporary SQLite database fixture.

### Wave 3: Failure Recovery & Resilience
* **Task 6.3: Resilience & Fault Tolerance Tests**
  * **File:** `tests/test_resilience.py`
  * **Scope:**
    * **Simulated Hardware Disconnect**: Mid-scan `OSError("Network is unreachable")` verification. Ensure lock is released and subsequent scans succeed.
    * **Concurrent Race Conditions**: Rapid parallel calls to `POST /api/scan`. Verify exactly one 202 and all others receive 409.
    * **Subnet Stress Simulation**: Mock 254 responding devices. Verify memory safety and serialization performance under 100ms.
    * **Missing Driver Recovery**: Scapy `PermissionError` handled without crashing WSGI server.
  * **Verification:** All resilience scenarios pass and recover gracefully.

### Wave 4: Full Suite Execution & Audit
* **Task 6.4: Comprehensive Test Run & Coverage Audit**
  * **Commands**:
    * `python -m pytest tests/ -v`
    * `python -m pytest tests/ --cov=scanner --cov=services --cov=database --cov=api --cov=utils --cov-report=term-missing`
  * **Target**: Zero test failures, ≥90% line coverage across operational modules.

* **Task 6.5: Roadmap & State Updates**
  * **Files:** `README.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`
  * **Scope:** Document test metrics and transition to Phase 7.

---

## 3. Acceptance Criteria Checklist

- [ ] Defensive CIDR validation in `POST /api/scan` rejects malformed inputs with 400.
- [ ] End-to-end integration tests verify complete pipeline (scan -> db -> API).
- [ ] Multi-scan state changes (online -> offline, first_seen preservation) verified end-to-end.
- [ ] System recovers cleanly after simulated adapter disconnection or Scapy permission failure.
- [ ] High-density subnet scan (250+ devices) executes cleanly under 100ms.
- [ ] All new integration and resilience tests pass hermetically.
- [ ] Full test suite passes 100% with zero regressions.
