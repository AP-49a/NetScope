# Phase 1 Research: Environment Setup and Network Fundamentals

## 1. Domain & Platform Realities (Windows 11)

### Interface Introspection
- Standard Windows networking does not require admin privileges to inspect adapter status, IP addresses, or MAC addresses if using system APIs.
- `psutil` wraps Windows API calls (`GetAdaptersAddresses`, `GetIfTable`) and exposes `net_if_stats()` and `net_if_addrs()`.
- Adapter naming in Windows 11 includes descriptive aliases like `"Ethernet"`, `"Wi-Fi"`, `"vEthernet (Default Switch)"`, and `"Loopback Pseudo-Interface 1"`.
- Heuristic string matching distinguishes physical Ethernet, Wi-Fi, and virtual hypervisor adapters.

### Gateway Detection
- `psutil` provides address and link statistics but does not expose default route gateways.
- Standard approach on Windows: parse `route print 0.0.0.0` output or query the routing table via subprocess.
- Pattern matching regex `^\s*0\.0\.0\.0\s+0\.0\.0\.0\s+(\d{1,3}(?:\.\d{1,3}){3})` extracts the primary gateway address accurately.

### CIDR & Subnet Calculations
- Python's standard library `ipaddress` provides `IPv4Network(f"{ip}/{mask}", strict=False)`.
- Using `strict=False` automatically zeroes the host bits to yield the canonical network CIDR block (e.g. `192.168.1.45/24` -> `192.168.1.0/24`).

### Logging & File Isolation
- Centralized logger using `logging.handlers.RotatingFileHandler` with fallback.
- When file operations are restricted by sandboxes or permissions, the logger must degrade gracefully to stdout/stderr stream handling without halting application logic.

---

## 2. Testability & Mocking Architecture
- By isolating OS queries (`psutil.net_if_stats`, `psutil.net_if_addrs`, and `subprocess.run`), all unit tests run offline in sub-second time without contacting the physical network or modifying local adapter state.
