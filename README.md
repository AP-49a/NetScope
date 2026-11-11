# NetScope

A locally hosted web application for discovering and monitoring devices on your local network.

> **Phase 1 complete.** The project foundation — environment, configuration, interface detection, network analysis, and tests — is in place. Device discovery and the web UI are coming in Phase 2+.

---

## Table of Contents

- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Npcap Installation](#npcap-installation-required-for-phase-2)
- [Known Limitations](#known-limitations)
- [Development Roadmap](#development-roadmap)

---

## Requirements

| Requirement | Version |
|---|---|
| Operating System | Windows 11 |
| Python | 3.11 or later (3.14 used in development) |
| Npcap | Latest release *(Phase 2 only)* |

---

## Quick Start

### 1. Clone the repository

```powershell
git clone https://github.com/your-username/netscope.git
cd netscope
```

### 2. Create and activate a virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

> **PowerShell execution policy:** If you see a script execution error, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

```powershell
Copy-Item .env.example .env
# Edit .env with your preferred settings (optional for Phase 1)
```

### 5. Verify network detection (Phase 1 demo)

```powershell
python -c "
from scanner.network import get_network_config
cfg = get_network_config()
if cfg:
    print(f'Interface : {cfg.interface_name}')
    print(f'IP        : {cfg.ip_address}')
    print(f'Mask      : {cfg.subnet_mask}')
    print(f'Gateway   : {cfg.gateway}')
    print(f'CIDR      : {cfg.cidr}')
else:
    print('No active network interface found.')
"
```

---

## Project Structure

```
netscope/
├── app.py               Flask entry point (Phase 2)
├── config.py            Centralised env-based configuration
├── requirements.txt     Pinned dependencies
├── .env.example         Environment variable template
├── .gitignore
├── README.md
│
├── scanner/
│   ├── interface.py     Interface enumeration & classification  ✅
│   ├── network.py       IP / mask / gateway / CIDR detection   ✅
│   └── discovery.py     ARP scan stub (Phase 2)                🔲
│
├── api/
│   └── routes.py        Flask Blueprint stub (Phase 2)          🔲
│
├── database/
│   ├── db.py            SQLite connection stub (Phase 2)        🔲
│   └── models.py        ORM model stubs (Phase 2)              🔲
│
├── utils/
│   └── logger.py        Rotating file + console logger         ✅
│
├── templates/
│   └── index.html       Placeholder HTML template
│
├── static/
│   ├── css/style.css    Placeholder stylesheet
│   └── js/app.js        Placeholder JavaScript
│
├── tests/
│   ├── conftest.py      pytest session configuration
│   ├── test_interface.py Interface tests (28 tests)            ✅
│   └── test_network.py  Network tests (29 tests)               ✅
│
├── logs/                Rotating logs (git-ignored)
└── docs/
    ├── architecture.md
    └── development-roadmap.md
```

---

## Configuration

All settings are read from environment variables. Copy `.env.example` to `.env` and edit as needed.

| Variable | Default | Description |
|---|---|---|
| `FLASK_HOST` | `127.0.0.1` | Bind address for the Flask server |
| `FLASK_PORT` | `5000` | Port for the Flask server |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |
| `SECRET_KEY` | *(dev key)* | Flask session secret |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `PREFERRED_INTERFACE` | *(auto)* | Force a specific interface name |
| `SCAN_TIMEOUT` | `2` | ARP scan timeout in seconds (Phase 2) |
| `DATABASE_PATH` | `netscope.db` | SQLite database path relative to project root |

---

## Running Tests

```powershell
# From the project root with the venv active:
python -m pytest tests/ -v
```

Expected output: **57 passed**.

To also see coverage:
```powershell
python -m pytest tests/ -v --cov=scanner --cov=utils --cov-report=term-missing
```

---

## Npcap Installation (required for Phase 2)

ARP scanning requires raw socket access provided by Npcap.

1. Download the latest Npcap installer from [npcap.com](https://npcap.com/#download).
2. Run the installer **as Administrator**.
3. During installation, enable:
   - ☑ **Install Npcap in WinPcap API-compatible Mode** (required for Scapy compatibility).
4. Restart your machine or reload the Npcap service:
   ```powershell
   net stop npcap
   net start npcap
   ```
5. Verify Scapy can see your interfaces:
   ```powershell
   python -c "from scapy.all import get_if_list; print(get_if_list())"
   ```

> **Administrator privileges:** ARP scanning with Scapy requires either running as Administrator or membership in the `Npcap Users` group.

---

## Known Limitations

| Limitation | Workaround / Future fix |
|---|---|
| Gateway detection relies on `route.exe` | Not an issue on standard Windows installs |
| Interface classification uses name heuristics | Exotic adapters fall back to `UNKNOWN`; set `PREFERRED_INTERFACE` |
| `venv/` created by a different Python install may be inaccessible | Delete and recreate with `python -m venv venv` |
| ARP scanning requires Npcap and admin rights | Phase 2; documented in this README |
| No live scanning in Phase 1 | Phase 2 |
| No web UI in Phase 1 | Phase 4 |

---

## Development Roadmap

See [`docs/development-roadmap.md`](docs/development-roadmap.md) for the full six-phase plan.

| Phase | Description | Status |
|---|---|---|
| 1 | Environment & Architecture | ✅ Complete |
| 2 | Network Discovery Engine | 🔲 |
| 3 | REST API & Flask Backend | 🔲 |
| 4 | Frontend UI | 🔲 |
| 5 | Persistent History | 🔲 |
| 6 | Polish & Production Hardening | 🔲 |
