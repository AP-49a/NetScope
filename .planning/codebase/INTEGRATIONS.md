# NetScope — Integrations & External Interfaces

## 1. Overview
NetScope is designed to run locally on Windows 11 with minimal external runtime dependencies. It interfaces directly with Windows kernel drivers, networking subsystems, the local filesystem, and local loopback HTTP clients.

---

## 2. Windows 11 Operating System & Drivers

### 2.1 Npcap Packet Capture Driver
- **Purpose**: Raw Layer 2 Ethernet packet transmission and packet sniffing.
- **Integration Mechanism**: Scapy binds to Npcap DLLs (`Packet.dll`, `wpcap.dll`) on Windows.
- **Requirements**:
  - Npcap installed with "Install Npcap in WinPcap API-compatible Mode".
  - Windows Administrator privileges required for raw packet construction.
- **Failure Mode & Handling**:
  - If Npcap or elevated privileges are absent, Scapy raises `PermissionError` or `Scapy_Exception`.
  - Caught by `scanner/discovery.py` and returned as a structured error message (`ScanResult.error_message`), preventing server crashes and alerting the user with actionable instructions.

### 2.2 Windows Routing Subsystem (`route.exe`)
- **Purpose**: Resolution of the primary default gateway IPv4 address.
- **Integration Mechanism**: Invokes `route print 0.0.0.0` via standard library `subprocess.run(..., capture_output=True, text=True)`.
- **Parsing**: Regular expression parsing identifies the active interface gateway row (`0.0.0.0 0.0.0.0 <gateway_ip> <interface_ip> <metric>`).
- **Resilience**: If parsing fails or command returns non-zero, safely returns `None`.

### 2.3 Network Adapter Subsystem via `psutil`
- **Purpose**: Adapter discovery, link status inspection, and IPv4 address extraction.
- **Integration Mechanism**:
  - `psutil.net_if_stats()`: Reads operational status (`isup`), duplex mode, and speed.
  - `psutil.net_if_addrs()`: Reads assigned IPv4, IPv6, and hardware MAC addresses.
- **Heuristics**: Classifies adapters into `InterfaceKind` (`WIFI`, `ETHERNET`, `LOOPBACK`, `VIRTUAL`, `UNKNOWN`) based on system name patterns.

---

## 3. Network Protocol Integrations

### 3.1 Address Resolution Protocol (ARP / Ether)
- **Protocol**: Layer 2 Ethernet broadcast (`Ether / ARP`).
- **Target**: Local CIDR subnet (e.g. `192.168.1.0/24`).
- **Scope**: Broadcast frames do not cross Layer 3 routing boundaries. Confined strictly to the local network segment.

### 3.2 Domain Name System (Reverse DNS / PTR)
- **Protocol**: Unicast UDP 53 reverse DNS lookups.
- **Mechanism**: `socket.gethostbyaddr(ip)` inside a thread pool with a strict 1.0-second timeout.
- **Fallback**: Gracefully falls back to `None` if local DNS / home router does not maintain PTR records for DHCP leases.

### 3.3 IEEE OUI & Private MAC Resolution
- **Protocol**: IEEE 802 Organizationally Unique Identifier lookups.
- **Mechanism**: Offline dictionary matching normalized 6-character hex prefixes against hardware vendors.
- **Privacy Extension**: Detects IEEE Locally Administered Address (LAA) bit (second digit in `[2, 6, A, E]`) indicating randomized MAC addresses used by modern iOS and Android devices.

---

## 4. Local Database & Filesystem

### 4.1 SQLite Embedded Database
- **File**: `netscope.db` (configurable via `DATABASE_PATH`).
- **Concurrency Mode**: Write-Ahead Logging (`WAL`), allowing concurrent HTTP queries during active scan writes.
- **Transactions**: Python context manager (`get_db_connection`) enforcing transactional rollbacks on exceptions and foreign key constraints.

### 4.2 Logging Subsystem
- **File**: `logs/netscope.log` via standard library `logging.handlers.RotatingFileHandler`.
- **Rotation**: 5 MB file size limit with 3 rotating backups.
- **Resilience**: Fallback to console-only stream logging if the target log directory is not writable.
