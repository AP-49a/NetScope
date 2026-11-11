# NetScope — Architectural Design

## 1. Architectural Philosophy
NetScope follows a modular, layered service-oriented architecture designed for lightweight local network observability. The system emphasizes clear separation of concerns, strong typing, zero-dependency calculation utilities where possible, and strict isolation between hardware-dependent network operations and presentation logic.

## 2. Layered Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  - templates/index.html (HTML5 Shell)                       │
│  - static/css/style.css (Dark-mode responsive design)       │
│  - static/js/app.js (Asynchronous fetch & DOM rendering)    │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
┌──────────────────────────────▼──────────────────────────────┐
│                      Web & API Layer                        │
│  - app.py (Flask application factory & server entry point)  │
│  - api/routes.py (Flask Blueprint: /api/network/config...)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ Internal Python Calls
┌──────────────────────────────▼──────────────────────────────┐
│                    Scanner & Domain Layer                   │
│  - scanner/network.py (CIDR, mask math, gateway resolution) │
│  - scanner/interface.py (psutil enumeration & priority)     │
│  - scanner/discovery.py (ARP-based scanning engine - Ph 2)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│      Persistence Layer      │ │      System & Utils         │
│  - database/db.py           │ │  - utils/logger.py (Rot. log)│
│  - database/models.py       │ │  - config.py (Env loader)   │
│  - netscope.db (SQLite3)    │ │  - Windows APIs / psutil    │
└─────────────────────────────┘ └─────────────────────────────┘
```

## 3. Component Details & Data Contracts

### Interface Introspection (`scanner/interface.py`)
- **Data Model**: `InterfaceInfo`
  - `name: str`
  - `kind: InterfaceKind` (`LOOPBACK`, `ETHERNET`, `WIFI`, `VIRTUAL`, `UNKNOWN`)
  - `is_up: bool`
  - `ipv4_address: Optional[str]`
  - `ipv4_netmask: Optional[str]`
  - `mac_address: Optional[str]`
  - `flags: list[str]`
  - Computed property: `is_active -> is_up and ipv4_address is not None`
- **Priority Selection Pipeline (`get_preferred_interface`)**:
  1. User explicit configuration (`PREFERRED_INTERFACE` in `.env`).
  2. First active physical Ethernet adapter.
  3. First active Wi-Fi adapter.
  4. Any non-loopback, non-virtual active adapter.
  5. Fallback: `None`.

### Network Calculation (`scanner/network.py`)
- **Data Model**: `NetworkConfig`
  - `interface_name: str`
  - `ip_address: Optional[str]`
  - `subnet_mask: Optional[str]`
  - `gateway: Optional[str]`
  - `cidr: Optional[str]`
  - `prefix_length: Optional[int]`
  - Computed property: `is_complete -> bool`
- **Pure Calculation Functions**:
  - `netmask_to_prefix_length(netmask: str) -> Optional[int]`
  - `calculate_cidr(ip_address: str, netmask: str) -> Optional[str]`
  - Strips host bits cleanly using `ipaddress.IPv4Network(..., strict=False)`.

## 4. Cross-Cutting Concerns

### Error Handling & Degradation Strategy
- Functions never crash the caller when encountering missing hardware, offline adapters, or restricted permissions.
- Network and interface detection modules return `None` or structured partial configurations rather than raising unhandled exceptions.
- Incomplete configurations are flagged via logging without terminating application workflows.

### Logging Architecture
- Double-dispatch logging: standard output stream handler + rotating file handler (`5 MB` max size, `3` backups).
- Fallback resilience: If write access to `logs/netscope.log` fails due to sandbox isolation or permission locks, the file handler fails gracefully and operational logging continues on console.
