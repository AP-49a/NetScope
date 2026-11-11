# NetScope — Architecture Concerns & Risk Analysis

## 1. Technical Debt & Current Shortcuts

### Gateway Discovery via `route print`
- Current implementation in `scanner/network.py` relies on `subprocess.run(["route", "print", "0.0.0.0"])`.
- **Risks**:
  - Requires Windows command line binary `route.exe` in `PATH`.
  - Fragile if Windows modifies default output table format in future OS updates.
  - Multi-homed gateways: In multi-gateway topologies, the regex takes the first matched line without comparing route metric costs.
- **Remediation Plan**: In Phase 2/3, consider fallback or native Windows IP Helper API (`GetAdaptersAddresses` / `GetBestRoute2`) or Scapy's internal routing table introspection (`scapy.arch.windows.get_windows_if_list()`).

### Adapter Classification Heuristics
- Heuristic string matching in `_classify_interface()` categorizes adapters using regex patterns on adapter display names (e.g., `wi-fi`, `ethernet`, `vethernet`).
- **Risks**: Non-English localized Windows installations may name adapters differently (e.g. German "WLAN" vs "Drahtlosnetzwerkverbindung"), resulting in `UNKNOWN` classification.
- **Mitigation**: Users can explicitly configure `PREFERRED_INTERFACE` in `.env`.

## 2. Platform & Environment Constraints

### Windows 11 & Npcap Requirement
- While Phase 1 operates without driver dependencies, Phase 2 ARP scanning with Scapy strictly requires Npcap with WinPcap API-compatible mode.
- Users must be instructed on Npcap installation and Windows firewall permissions.
- Scapy packet injection requires Administrator elevation or adding the local user to the `Npcap Users` security group.

### Python 3.14 Environment Peculiarities
- Development environment currently utilizes Python 3.14.6.
- Some legacy C-extension packages may not have pre-built binary wheels for Python 3.14 yet. Current dependencies (`psutil`, `flask`, `scapy`) have verified compatibility, but future additions must be checked.

## 3. Security Considerations

### Local Binding & Scope
- Flask development server binds to `FLASK_HOST=127.0.0.1` by default.
- If bound to `0.0.0.0`, the unauthenticated discovery endpoints and device inventory would be exposed across the LAN.
- Phase 2+ must ensure CORS policies and bind defaults remain safe for single-machine local hosting.

### Network Traffic & ARP Flooding
- Unthrottled ARP scanning in Phase 2 across large subnets (e.g. `/16` with 65,534 hosts) could flood local networks or trigger IDS/firewall alerts.
- **Guardrail**: Subnet scanning should be restricted to `/24` (or max 256-512 hosts) or require explicit confirmation for broader CIDR blocks.

## 4. Phase 2 Readiness Matrix

| Feature / Subsystem | Phase 1 Status | Phase 2 Action Item |
|---|---|---|
| Interface Detection | Ready | Connect chosen interface into Scapy `conf.iface` |
| CIDR Math | Ready | Feed computed CIDR into ARP `Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=cidr)` |
| Database Storage | Stubs | Design SQLite schema (`devices`, `scan_history`) |
| API Layer | Stubs | Implement `/api/network/config` and `/api/scan` routes |
| Web UI | Shells | Connect frontend fetch loop to Flask endpoints |
