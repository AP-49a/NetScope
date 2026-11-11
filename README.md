# NetScope 🌐

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-username/netscope)
[![Python](https://img.shields.io/badge/python-3.11%2B-brightgreen.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-119%20passed-success.svg)]()
[![Coverage](https://img.shields.io/badge/coverage-92%25-brightgreen.svg)]()

**NetScope** is a local-first network discovery and device monitoring web application designed specifically for Windows 11. Built with Python, Flask, Scapy, SQLite, and vanilla frontend technologies, NetScope provides deep visibility into your authorized local subnet without requiring complex command-line utilities or third-party cloud telemetry.

---

## 🌟 Key Features

- **Automatic Interface & Subnet Discovery**: Detects active physical network adapters (Wi-Fi, Ethernet), resolves the default gateway using Windows routing tables, and calculates exact subnet CIDR boundaries.
- **Scapy ARP Broadcast Engine**: Fast, non-blocking address resolution protocol (ARP) scanning across local subnet segments.
- **OUI Manufacturer Identification**: Offline MAC prefix database identifying device manufacturers (Apple, Intel, Samsung, Dell, Raspberry Pi, TP-Link, etc.) without external API latency.
- **Reverse DNS Hostname Resolution**: Automatically attempts hostname resolution for responding IP addresses with thread-bounded timeouts.
- **Persistent Device Inventory**: SQLite database in Write-Ahead Logging (WAL) mode tracks devices across scans, accurately recording initial discovery (`first_seen`), most recent activity (`last_seen`), and availability (`online` / `offline`).
- **Interactive Dark Dashboard**: High-contrast, responsive interface with real-time progress indicators, search/filter controls, and a historical scan log modal.
- **Self-Contained Preflight Launcher**: Automated environment verification validating Python version, dependencies, SQLite schema, and packet capture driver availability.

---

## 📐 System Architecture

```
Browser Client (http://127.0.0.1:5000)
       │
       ▼
Flask Web Server (app.py) ── REST API (api/routes.py)
       │
       ▼
Scan Service Coordinator (services/scan_service.py) ── Concurrency Mutex Lock
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
Scanner Engine (scanner/)       Database Storage (database/)
├── interface.py (psutil)       ├── db.py (SQLite WAL Mode)
├── network.py (ipaddress)      └── models.py (Devices & History)
├── discovery.py (Scapy ARP)
├── oui.py (Hardware Vendors)
└── hostname.py (Reverse DNS)
```

---

## 💻 Prerequisites

| Component | Minimum Requirement | Notes |
|---|---|---|
| **Operating System** | Windows 11 / Windows 10 (64-bit) | Tested on Windows 11 AMD64 |
| **Python** | 3.11 or later | Python 3.14 compatible |
| **Packet Capture** | **Npcap** (Recommended) | Required for Scapy raw ARP packet injection |
| **User Privileges** | Administrator | Elevated terminal required for raw socket access |

---

## 📥 Npcap Installation Guide

NetScope uses Scapy to transmit raw Layer 2 ARP frames. On Windows, this requires the **Npcap** packet capture driver.

1. Download the Npcap installer from the official website:  
   👉 **[https://npcap.com/#download](https://npcap.com/#download)**
2. Run the installer (`npcap-x.xx.exe`).
3. **Important Installation Checkbox**:
   - ✅ Ensure **"Install Npcap in WinPcap API-compatible Mode"** is checked.
4. Complete the installation and reboot if prompted.

> **Administrator Privileges:** Due to Windows raw socket security boundaries, your terminal or command prompt must be launched with **"Run as Administrator"** when scanning the network.

---

## 🚀 Quick Start

### 1. Clone the Repository
```powershell
git clone https://github.com/your-username/netscope.git
cd netscope
```

### 2. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell blocks execution of scripts, run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`)*

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Configure Environment
```powershell
Copy-Item .env.example .env
```
*(Default settings bind to `127.0.0.1:5000` and use `netscope.db`)*

### 5. Launch NetScope
You can launch NetScope using the automated preflight launcher or the Windows batch runner:

**Option A: Python Launcher (Recommended)**
```powershell
python run.py
```

**Option B: Windows Batch Runner**
```cmd
run.bat
```

Once started, open your web browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 📡 REST API Reference

NetScope provides a local JSON API. For detailed schema documentation, refer to **[docs/api.md](docs/api.md)**.

| Endpoint | Method | Description |
|---|---|---|
| `/api/network` | `GET` | Retrieves active network interface, host IP, subnet mask, and CIDR |
| `/api/scan` | `POST` | Initiates asynchronous ARP sweep (optional `cidr` and `timeout`) |
| `/api/status` | `GET` | Returns scanning state (`idle`, `scanning`, `completed`, `error`) |
| `/api/devices` | `GET` | Returns list of tracked devices with status and timestamp history |
| `/api/history` | `GET` | Returns audit log of previous scan sessions |

---

## 🛠️ Troubleshooting & FAQ

### 1. `PermissionError` or "Scapy requires administrative privileges"
- **Cause:** Windows prevents non-elevated user accounts from creating raw Layer 2 network sockets.
- **Fix:** Close your terminal, right-click **PowerShell** or **Command Prompt**, choose **"Run as administrator"**, navigate back to `c:\codes\netscope`, activate your venv, and run `python run.py`.

### 2. `Scapy_Exception: Sniffing and sending packets is not available`
- **Cause:** Npcap is either not installed or was installed without WinPcap compatibility.
- **Fix:** Reinstall Npcap from [npcap.com](https://npcap.com/#download) with the **"Install Npcap in WinPcap API-compatible Mode"** checkbox enabled.

### 3. Only the local computer and default gateway appear in scans
- **Cause:** Many modern home or corporate Wi-Fi routers enable **AP Isolation** (Client Isolation) preventing Wi-Fi devices from seeing one another, or target devices have strict local firewalls that reject ARP queries.
- **Fix:** Ensure you are on a trusted local network. If using Wi-Fi, test via Ethernet or check router settings for "AP Isolation".

### 4. Port 5000 is already in use
- **Cause:** Another application is occupying TCP port 5000.
- **Fix:** Set a custom port in your `.env` file (`PORT=5050`) or run with `PORT=5050 python run.py`.

---

## ⚠️ Important Limitations

In alignment with responsible network discovery principles:
1. **Local Subnet Scope:** NetScope uses ARP broadcast packets which do not cross Layer 3 routing boundaries. Scans are strictly confined to the local subnet segment.
2. **Honest Reporting:** NetScope only reports verifiable attributes. When a hostname or manufacturer cannot be resolved, it is reported as `Unknown` rather than synthesized.
3. **Out of MVP Scope:** Port scanning, deep packet inspection, automated device disconnection, and remote cloud synchronization are deliberately excluded from this release.

---

## 🧪 Running Automated Tests

NetScope includes a hermetic test suite with unit, integration, and stress tests.

```powershell
# Run full test suite
pytest tests/ -v

# Run with test coverage report
pytest tests/ --cov=scanner --cov=services --cov=database --cov=api --cov=utils --cov-report=term-missing
```

Current test status: **119 passed, 0 failures, 92% statement coverage**.

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
