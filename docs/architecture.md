# NetScope — Architecture Documentation

## Project Overview

NetScope is a locally hosted web application for discovering and monitoring devices connected to a local network. It runs on Windows 11 and is served through a local Flask server.

---

## High-Level Architecture

```
Browser (localhost:5000)
        │
        ▼
  Flask (app.py)
        │
   ┌────┴────┐
   │  API     │  api/routes.py  ─── JSON responses
   └────┬────┘
        │
   ┌────▼────────────────────┐
   │  Scanner Layer          │
   │  scanner/interface.py   │  psutil — interface enumeration
   │  scanner/network.py     │  ipaddress, route — IP/mask/GW/CIDR
   │  scanner/discovery.py   │  Scapy+Npcap — ARP scan (Phase 2)
   └────┬────────────────────┘
        │
   ┌────▼────┐
   │Database │  database/db.py + models.py  ─── SQLite (Phase 2)
   └─────────┘
```

---

## Module Reference

### `config.py`
Centralised configuration. Reads all tuneable values from environment variables via `.env`. Exposes typed constants for every other module.

### `utils/logger.py`
Configures the Python root logger with:
- Formatted console output.
- Rotating file handler writing to `logs/netscope.log` (5 MB, 3 backups).
- Graceful fallback when the log directory is not writable.

Call `get_logger(__name__)` in every module.

### `scanner/interface.py`
Enumerates network interfaces via `psutil`. Classifies each as `LOOPBACK`, `ETHERNET`, `WIFI`, `VIRTUAL`, or `UNKNOWN` using name-pattern heuristics. Exposes:

| Function | Purpose |
|---|---|
| `list_interfaces()` | All interfaces (active and inactive) |
| `list_active_interfaces()` | Interfaces that are UP with an IPv4 address |
| `get_preferred_interface(name)` | Best interface for outbound traffic |

### `scanner/network.py`
Derives network configuration from an active interface. Exposes:

| Function | Purpose |
|---|---|
| `netmask_to_prefix_length(mask)` | `'255.255.255.0'` → `24` |
| `calculate_cidr(ip, mask)` | `'192.168.1.5', '255.255.255.0'` → `'192.168.1.0/24'` |
| `get_default_gateway()` | Parses `route print 0.0.0.0` |
| `get_network_config(preferred)` | Complete `NetworkConfig` for the best interface |
| `get_all_network_configs()` | One `NetworkConfig` per active interface |

### `scanner/discovery.py`
**Stub — Phase 2.** Will implement ARP-based device discovery using Scapy.

### `api/routes.py`
**Stub — Phase 2.** Flask Blueprint with JSON API endpoints.

### `database/`
**Stub — Phase 2.** SQLite schema management and ORM models.

### `app.py`
**Stub — Phase 2.** Flask application factory and dev-server entry point.

---

## Data Flow (Phase 1)

```
psutil.net_if_stats()
psutil.net_if_addrs()
        │
        ▼
  list_interfaces()
        │
        ▼
  get_preferred_interface()     ◄── PREFERRED_INTERFACE env var
        │
        ├──► ipv4_address
        ├──► ipv4_netmask
        │
        ▼
  route print 0.0.0.0
        │
        ├──► gateway
        │
        ▼
  calculate_cidr(ip, mask)
        │
        ▼
  NetworkConfig(interface, ip, mask, gateway, cidr, prefix_length)
```

---

## Dependency Map

| Package | Version | Purpose | Phase |
|---|---|---|---|
| `flask` | 3.1.3 | Web framework | 2 |
| `flask-cors` | 6.0.5 | CORS headers | 2 |
| `psutil` | 7.2.2 | Interface enumeration | **1** |
| `scapy` | 2.8.0 | ARP packet crafting | 2 |
| `python-dotenv` | 1.2.4 | `.env` loading | **1** |
| `pytest` | 9.2.0 | Test runner | **1** |
| `pytest-cov` | 6.1.0 | Coverage reports | **1** |

---

## Directory Layout

```
netscope/
├── app.py               Flask entry point (Phase 2 stub)
├── config.py            Centralised env-based config
├── requirements.txt     Pinned dependencies
├── .env.example         Environment variable template
├── .gitignore
├── README.md
│
├── scanner/
│   ├── interface.py     ✅ Interface enumeration & classification
│   ├── network.py       ✅ IP / mask / gateway / CIDR detection
│   └── discovery.py     🔲 ARP scan stub (Phase 2)
│
├── api/
│   └── routes.py        🔲 Flask Blueprint stub (Phase 2)
│
├── database/
│   ├── db.py            🔲 SQLite stub (Phase 2)
│   └── models.py        🔲 ORM models stub (Phase 2)
│
├── utils/
│   └── logger.py        ✅ Rotating file + console logger
│
├── templates/
│   └── index.html       Placeholder HTML
│
├── static/
│   ├── css/style.css    Placeholder CSS
│   └── js/app.js        Placeholder JS
│
├── tests/
│   ├── conftest.py      pytest session config
│   ├── test_interface.py ✅ 28 tests
│   └── test_network.py  ✅ 29 tests
│
├── logs/                Rotating log files (git-ignored)
└── docs/                Architecture & roadmap
```

---

## Design Decisions

### Why `psutil` for interface detection?
- Cross-platform, no admin privileges required on Windows.
- Provides interface stats (UP/DOWN), addresses, and flags in one call.
- Avoids `subprocess` calls to `ipconfig` which are fragile to locale changes.

### Why `route print` for gateway detection?
- `psutil` does not expose the default gateway.
- `route print 0.0.0.0` is consistent across all Windows versions.
- No third-party dependency required.
- Parsed with a narrow regex; locale-independent for the IP columns.

### Why `ipaddress` stdlib for CIDR calculation?
- Built into Python 3.3+; no extra dependency.
- `IPv4Network(strict=False)` handles host bits automatically.

### Why name-pattern heuristics for interface classification?
- Windows does not expose a reliable interface-type enum via `psutil`.
- Heuristics cover the common cases (Wi-Fi, Ethernet, Hyper-V, WSL, Docker).
- Unrecognised interfaces fall back to `UNKNOWN`; callers decide what to do.
