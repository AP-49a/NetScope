# Phase 2 Plan: Core Network Scanning Engine

## Phase Objective
Implement an ARP-based local network device discovery engine using Scapy, resolving IP addresses, MAC addresses, hostnames, and MAC OUI manufacturers, complete with error handling, timing metrics, and offline unit test coverage.

**Phase Directory:** `.planning/phases/02-network-scanning-engine`  
**Status:** **Ready for Execution**  

---

## 1. Architectural Scope & Guardrails

```
┌─────────────────────────────────────────────────────────────┐
│                       In Scope (Phase 2)                    │
├─────────────────────────────────────────────────────────────┤
│ • Scapy ARP request/reply generation (scanner/discovery.py) │
│ • DiscoveredDevice & ScanResult dataclasses                 │
│ • MAC OUI manufacturer offline lookup utility (scanner/oui) │
│ • Non-blocking / bounded hostname reverse DNS resolution    │
│ • Duration measurement & configurable timeouts              │
│ • Exception handling for Npcap / permission constraints     │
│ • Automated unit tests with Scapy mocks (test_discovery.py) │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Locked Out (Phase 3+)                    │
├─────────────────────────────────────────────────────────────┤
│ ✕ Flask web endpoints or routing (Phase 3)                  │
│ ✕ Multi-threaded background scan service worker (Phase 3)   │
│ ✕ Frontend dashboard controls or visualization (Phase 4)    │
│ ✕ SQLite database persistence (Phase 5)                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Data Contracts

### 2.1 `DiscoveredDevice` Model
```python
@dataclass
class DiscoveredDevice:
    ip_address: str
    mac_address: str
    hostname: Optional[str] = None
    manufacturer: Optional[str] = None
    status: str = "online"

    def to_dict(self) -> dict[str, Any]:
        ...
```

### 2.2 `ScanResult` Model
```python
@dataclass
class ScanResult:
    cidr: str
    interface_name: str
    devices: list[DiscoveredDevice]
    duration_seconds: float
    started_at: str
    completed_at: str
    success: bool
    error_message: Optional[str] = None
```

---

## 3. Work Breakdown & Task Decomposition

### Wave 1: Foundation Helpers (OUI & Hostname)
* **Task 2.1: MAC OUI Manufacturer Lookup Module**
  * **File**: `scanner/oui.py`
  * **Responsibility**: Fast, offline OUI vendor lookup.
  * **Design**:
    - Pre-populate a curated dictionary of major networking and consumer device OUIs (Apple, Intel, Samsung, Cisco, Raspberry Pi, TP-Link, Espressif, Google, Amazon, Microsoft, Dell, HP, Netgear, ASUS, etc.).
    - Normalize MAC strings (e.g. `"aa:bb:cc:11:22:33"` -> `"AABBCC"`).
    - Function: `get_manufacturer(mac: str) -> Optional[str]`.
  * **Verification**: Unit tests with known MACs and random unassigned MACs.

* **Task 2.2: Hostname Resolution Helper**
  * **File**: `scanner/hostname.py` (or integrated into `scanner/discovery.py`)
  * **Responsibility**: Safe reverse DNS lookup with bounded timeout.
  * **Design**:
    - Function: `resolve_hostname(ip: str, timeout: float = 1.0) -> Optional[str]`.
    - Handles `(socket.herror, socket.gaierror, socket.timeout, OSError)`.
  * **Verification**: Mocked and real localhost IP resolution tests.

### Wave 2: Core Scanning Engine
* **Task 2.3: ARP Discovery Implementation**
  * **File**: `scanner/discovery.py`
  * **Responsibility**: Craft and transmit ARP packets via Scapy, collect responses, assemble `DiscoveredDevice` records.
  * **Design**:
    - Function: `scan_network(cidr: Optional[str] = None, interface_name: Optional[str] = None, timeout: Optional[float] = None) -> ScanResult`.
    - Automatically defaults to `get_network_config()` if `cidr` or `interface_name` are not provided.
    - Uses Scapy `Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst=cidr)`.
    - Captures duration via `time.perf_counter()`.
    - Handles Scapy exceptions (`PermissionError`, `Scapy_Exception`, missing Npcap) by returning a structured `ScanResult` with `success=False` and a clear error message.
  * **Verification**: Standalone execution with mocked Scapy engine.

### Wave 3: Testing & Integration Verification
* **Task 2.4: Hermetic Unit Tests**
  * **File**: `tests/test_discovery.py`
  * **Responsibility**: Comprehensive automated tests verifying discovery logic without live networking.
  * **Coverage**:
    - Normal discovery with multiple answering devices.
    - Empty network scan (no responses).
    - Permission error handling (simulating missing Npcap / non-admin).
    - Hostname resolution successes, failures, and timeouts.
    - OUI lookup edge cases (malformed MACs, broadcast addresses).
    - Scan duration calculation.
  * **Verification**: `python -m pytest tests/test_discovery.py -v` passes 100%.

* **Task 2.5: CLI Demo & Roadmap Update**
  * **Files**: `README.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`
  * **Responsibility**: Update project state and provide a one-line CLI test command for manual verification.

---

## 4. Acceptance Criteria Checklist

- [ ] `scanner/discovery.py` sends ARP requests and processes responses.
- [ ] Each discovered device contains `ip_address`, `mac_address`, `hostname`, `manufacturer`, and `status`.
- [ ] Hostname resolution and OUI lookups fail gracefully to `None` without crashing.
- [ ] Scan duration is accurately recorded in `ScanResult`.
- [ ] Missing Npcap or permission errors return a clean `ScanResult(success=False, error_message=...)`.
- [ ] Scanner is completely decoupled and testable independently of Flask.
- [ ] All new tests pass hermetically in `tests/test_discovery.py`.
- [ ] All 57 Phase 1 tests continue to pass without regressions.
