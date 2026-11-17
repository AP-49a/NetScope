# NetScope — Architecture Concerns & Limitations

## 1. Technical Boundaries & Hardware Constraints

### 1.1 Windows Raw Socket Elevation & Npcap
- **Constraint**: Windows security architecture prevents non-elevated user accounts from creating raw Layer 2 network sockets.
- **Impact**: Running scans requires Npcap installed with "Install Npcap in WinPcap API-compatible Mode" and launching the terminal or process as Administrator.
- **Mitigation**: `run.py` preflight launcher proactively checks for Administrator privileges and Npcap availability, presenting clear warnings rather than failing silently.

### 1.2 Layer 2 ARP Broadcast Scope
- **Constraint**: ARP frames are Layer 2 broadcast packets that do not cross Layer 3 routing boundaries.
- **Impact**: NetScope cannot discover devices located behind secondary routers, NAT gateways, or VLAN segments.
- **Design Principle**: Documented transparently as an architectural boundary in user documentation.

### 1.3 Mobile OS MAC Address Randomization
- **Constraint**: Modern mobile platforms (iOS 14+, Android 10+, Windows 11) randomize MAC addresses on Wi-Fi by default.
- **Impact**: Randomized MACs do not match IEEE hardware manufacturer OUI prefixes, and mobile devices block unauthenticated local incoming probes.
- **Mitigation**:
  - Implemented IEEE 802 Locally Administered Address (LAA) bit detection, explicitly labeling them as `Private MAC (Mobile/PC)`.
  - Added user-customizable device nicknames (`✏️ Name`) allowing users to label their phones and smart devices permanently.

### 1.4 Consumer Router Reverse DNS Limitations
- **Constraint**: Consumer Wi-Fi routers rarely run local DNS PTR resolvers for dynamic DHCP leases.
- **Impact**: Most client hostnames cannot be resolved via standard reverse DNS (`socket.gethostbyaddr`).
- **Mitigation**:
  - Automatically identifies the default gateway as `Router (Default Gateway)`.
  - Automatically identifies the host machine as `hostname (This PC)`.
  - Device nicknames saved in SQLite persist across subsequent network scans.

---

## 2. Security & Operational Boundaries

### 2.1 Default Localhost Binding
- **Design**: The Flask web application binds strictly to `127.0.0.1` by default.
- **Rationale**: Prevents exposing the network scanner and administrative API to external unauthorized networks.

### 2.2 Strict Out-of-Scope Capabilities
In accordance with `plan.md` MVP boundaries:
- **No Port Scanning or Vulnerability Probing**: Avoids triggering intrusion detection systems or violating network terms of service.
- **No Deep Packet Inspection (DPI)**: Preserves network performance and user privacy.
- **No Automated Packet Blocking or Firewall Alteration**: Avoids disruption of local network routing.
