# NetScope — Testing Patterns & Quality Assurance

## 1. Test Architecture

The NetScope automated test suite is built on **pytest** and **unittest.mock**.
Tests are completely hermetic: they do not interact with live network adapters, transmit packets, or require administrative privileges.

## 2. Test Suite Structure

```
tests/
├── __init__.py           # Package marker
├── conftest.py           # Session fixtures & isolated logging configuration
├── test_interface.py     # 28 tests for interface enumeration, classification, & preference
└── test_network.py       # 29 tests for IP/mask calculation, CIDR parsing, & gateway handling
```

Total Test Cases: **57 passed** in 0.20s.

## 3. Test Suites & Coverage

### `test_interface.py` (28 Tests)
- `TestClassifyInterface`: Verifies interface heuristic detection:
  - Loopback adapters (via psutil flag priority).
  - Virtual adapters (`vEthernet`, `VMware`, `Docker`, `WSL`).
  - Wi-Fi adapters (`Wi-Fi`, `Wireless Network Connection`, `WLAN0`).
  - Ethernet adapters (`Ethernet`, `Ethernet 2`, `Local Area Connection`, `eth0`).
  - Unrecognised adapter fallback (`UNKNOWN`).
- `TestInterfaceInfoIsActive`: Verifies `is_active` logic:
  - Active only when `is_up=True` AND `ipv4_address is not None`.
  - Inactive when interface is DOWN, missing an IP, or both.
- `TestListInterfaces`: Validates enumeration parsing using mocked `psutil.net_if_stats` and `psutil.net_if_addrs`.
- `TestListActiveInterfaces`: Verifies active filter across mixed interface lists.
- `TestGetPreferredInterface`: Validates auto-selection logic:
  - Explicit preference match (`PREFERRED_INTERFACE`).
  - Automatic fallback priority: Ethernet → Wi-Fi → Other Non-Virtual → None.
  - Graceful handling when only virtual or no interfaces exist.

### `test_network.py` (29 Tests)
- `TestNetmaskToPrefixLength`: Parametrized testing for netmasks (`/24`, `/16`, `/8`, `/25`, `/32`, `/0`), plus malformed input handling (`not-a-mask`, `999.0.0.0`, empty strings).
- `TestCalculateCidr`: Parametrized testing verifying host bits are stripped to calculate true network address (e.g. `192.168.1.5` + `255.255.255.0` → `192.168.1.0/24`).
- `TestNetworkConfig`: Dataclass attribute validation and `is_complete` boolean flag evaluation.
- `TestGetNetworkConfig`: Mocked integration tests verifying complete configuration generation, missing gateway handling, and missing adapter scenarios.
- `TestGetAllNetworkConfigs`: Multi-homed interface support verification.

## 4. Mocking Strategy & Patterns

- **Isolation from Live OS**:
  ```python
  @patch("scanner.network.get_default_gateway", return_value="192.168.1.1")
  @patch("scanner.network.list_active_interfaces", return_value=[...])
  def test_get_all_network_configs(...):
      ...
  ```
- **Mock Target Rules**:
  - Always patch imports where they are *used* (e.g., `scanner.network.list_active_interfaces`), not where they are defined, if imported directly.
- **Logging Redirection in Tests**:
  - `conftest.py` configures logging into a temporary directory created via `tmp_path_factory.mktemp("logs")` to avoid file write permission conflicts during automated test runs.

## 5. Execution Instructions

Run full test suite:
```powershell
python -m pytest tests/ -v
```

Run with coverage report:
```powershell
python -m pytest tests/ -v --cov=scanner --cov=utils --cov-report=term-missing
```

Disable pytest cache generation (useful in restricted write environments):
```powershell
python -m pytest tests/ -v -p no:cacheprovider
```
