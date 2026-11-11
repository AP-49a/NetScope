# NetScope — External & Internal Integrations

## 1. Internal Module Integration Map

NetScope follows a strictly decoupled layered architecture. Dependencies flow downwards towards utility and configuration layers.

```
       [app.py] (Application Factory & Server Entry Point)
          │
          ├───► [api/routes.py] (REST API Blueprint)
          │        │
          │        └───► [scanner/network.py] (Network Calculation & Config Detection)
          │                 │
          │                 ├───► [scanner/interface.py] (psutil Adapter Introspection)
          │                 │
          │                 └───► [scanner/discovery.py] (ARP Discovery Engine - Phase 2)
          │
          ├───► [database/db.py & models.py] (SQLite Persistence Layer - Phase 2)
          │
          ├───► [config.py] (Centralized Environment Configuration)
          │
          └───► [utils/logger.py] (Dual Console + Rotating File Logging)
```

### Module Boundaries & Coupling
- **`config.py`**:
  - Independent root module. Reads from `.env` via `python-dotenv`.
  - Exposes typed configuration variables: `FLASK_HOST`, `FLASK_PORT`, `LOG_FILE`, `PREFERRED_INTERFACE`, `DATABASE_PATH`.
- **`utils/logger.py`**:
  - Centralized logger factory.
  - Utilizes lazy imports of `config.LOG_LEVEL` and `config.LOG_FILE` to avoid circular import issues during module initialization.
  - Implements defensive logging fallbacks if log directories are unwritable or permission-constrained.
- **`scanner/interface.py`**:
  - Pure introspection of host adapters. Uses `psutil`.
  - Exports `InterfaceInfo` dataclass and `InterfaceKind` enum.
  - Decoupled from `scanner/network.py` and upper layers.
- **`scanner/network.py`**:
  - Builds upon `scanner/interface.py` to associate IP addresses and masks with routing information.
  - Exports `NetworkConfig` dataclass, `calculate_cidr`, `netmask_to_prefix_length`, `get_network_config`, and `get_all_network_configs`.

## 2. Operating System Integrations (Windows 11)

### Network Interface Enumeration via `psutil`
- Direct integration with Windows Network API bindings through `psutil.net_if_stats()` and `psutil.net_if_addrs()`.
- Captures:
  - Adapter operational status (`isup` flag).
  - Protocol families (`AF_INET` for IPv4, `AF_LINK` for MAC addresses).
  - Adapter descriptive names (`Ethernet`, `Wi-Fi`, `vEthernet (...)`, `Loopback Pseudo-Interface 1`).
- Operates entirely in user space without requiring UAC elevation.

### Windows Routing Table Introspection via `route.exe`
- Invocation: `subprocess.run(["route", "print", "0.0.0.0"], capture_output=True, text=True, timeout=5)`.
- Extraction:
  - Regex pattern matching `^\s*0\.0\.0\.0\s+0\.0\.0\.0\s+(\d{1,3}(?:\.\d{1,3}){3})` against routing table rows.
  - Identifies default gateway IP corresponding to 0.0.0.0/0 route.
  - Encapsulated with exception handling (`FileNotFoundError`, `TimeoutExpired`, `OSError`).

## 3. Future External Integrations (Phase 2+)

### Npcap Packet Capture Driver & Scapy
- **Scapy Integration**:
  - Scapy uses Npcap's DLL (`wpcap.dll` / `Packet.dll`) on Windows for sending raw Ethernet broadcast frames (ARP Request `who-has`).
  - Integration Requirement: Npcap installed in "WinPcap API-compatible Mode".
  - Permission Level: Administrator or user account belonging to `Npcap Users` security group.
- **SQLite Database**:
  - Integrated via standard library `sqlite3` connecting to `DATABASE_PATH`.
