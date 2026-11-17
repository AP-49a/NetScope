# NetScope — Testing & Quality Assurance Guide

## 1. Test Architecture & Organization

NetScope maintains a comprehensive, hermetic automated test suite using **pytest** and **pytest-cov**. The test suite runs in under 10 seconds and requires zero live network access or elevated privileges.

### Test Directory Layout
```
tests/
├── conftest.py          # Global test fixtures, logging redirection to temp directory
├── test_interface.py    # Interface enumeration & classification tests (13 tests)
├── test_network.py      # CIDR calculations & Windows route table parsing tests (29 tests)
├── test_discovery.py    # Scapy ARP packet parsing, OUI vendor, and hostname tests (33 tests)
├── test_api.py          # Flask routes, scan endpoints, and service lifecycle tests (15 tests)
├── test_frontend.py     # HTML structure, CSS rules, and JS integration tests (3 tests)
├── test_database.py     # SQLite schema, device upsert, first_seen, and history tests (7 tests)
├── test_integration.py  # End-to-end multi-scan pipeline lifecycle tests (1 test)
└── test_resilience.py   # Failure recovery, concurrency locks, and subnet stress (7 tests)
```

---

## 2. Test Execution & Coverage

### 2.1 Running Tests
```powershell
# Run the complete test suite
pytest tests/ -v

# Run with test coverage report
pytest tests/ --cov=scanner --cov=services --cov=database --cov=api --cov=utils --cov-report=term-missing
```

### 2.2 Coverage Metrics
- **Total Tests**: **130 passing tests** (100% pass rate).
- **Overall Statement Coverage**: **94%**.

| Module | Statements | Missing | Coverage |
|---|---|---|---|
| `api/routes.py` | 73 | 2 | 97% |
| `database/db.py` | 41 | 6 | 85% |
| `database/models.py` | 73 | 0 | 100% |
| `scanner/discovery.py` | 107 | 7 | 93% |
| `scanner/hostname.py` | 28 | 6 | 79% |
| `scanner/interface.py` | 107 | 4 | 96% |
| `scanner/network.py` | 102 | 6 | 94% |
| `scanner/oui.py` | 26 | 1 | 96% |
| `services/scan_service.py`| 84 | 9 | 89% |
| `utils/logger.py` | 36 | 2 | 94% |
| **TOTAL** | **677** | **43** | **94%** |

---

## 3. Testing Strategies & Patterns

### 3.1 Hermetic Isolation & Mocking
- **No Live Raw Sockets**: Scapy's `srp()` is mocked using `unittest.mock.patch` with synthetic `_build_arp_response()` tuples simulating real `Ether/ARP` packet replies.
- **Database Isolation**: Tests execute against temporary SQLite databases (`tmp_path / "test.db"`) created and discarded per test function or class.
- **OS Subprocess Mocking**: `route print` and `psutil` system calls are mocked with canned platform data.

### 3.2 Resilience & Stress Testing (`tests/test_resilience.py`)
- **Simulated Hardware Disconnection**: Injects `OSError("Network is unreachable")` mid-scan to verify that the scanner transitions cleanly to error state, releases its concurrency lock, and accepts subsequent scans when network returns.
- **Burst Concurrency**: Submits 10 simultaneous threads calling `POST /api/scan` to verify single-writer mutual exclusion (strictly 1 receives `202`, 9 receive `409`).
- **High-Density Subnet Stress**: Tests batch database insertion of 254 simulated host records to verify response times and memory safety.
