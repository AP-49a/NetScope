# Phase 2 Research: Core Network Scanning Engine

## 1. Domain & Technology Research

### 1.1 ARP-Based Discovery via Scapy
- **ARP Mechanism**: Address Resolution Protocol operates at Layer 2 (Data Link) and Layer 3 (Network). An ARP request packet is broadcasted (`ff:ff:ff:ff:ff:ff`) asking `"Who has IP X.X.X.X? Tell Y.Y.Y.Y"`. The device owning that IP responds with an ARP reply containing its hardware (MAC) address.
- **Scapy Packet Crafting**:
  ```python
  from scapy.all import Ether, ARP, srp, conf
  ether = Ether(dst="ff:ff:ff:ff:ff:ff")
  arp = ARP(pdst=cidr)
  packet = ether / arp
  ans, unans = srp(packet, timeout=timeout, iface=iface_name, verbose=False)
  ```
- **Scapy Windows Driver**:
  - Scapy utilizes Npcap for raw packet capture and transmission on Windows.
  - Interface selection: `conf.iface` or passing explicit `iface` parameter. Windows interface names in Scapy may map to Npcap device names (e.g., `\\Device\\NPF_{GUID}`) or Windows friendly names (`"Wi-Fi"`, `"Ethernet"`). Scapy 2.5+ automatically maps Windows friendly names when Npcap is present.
  - Privilege constraint: Raw socket transmission on Windows requires either Administrative elevation or membership in the `Npcap Users` group. If privileges or Npcap are absent, Scapy raises `Scapy_Exception` or `PermissionError`. The scanner must capture this defensively and return structured error diagnostics.

### 1.2 Hostname Resolution
- Standard library `socket.gethostbyaddr(ip)`:
  - Performs reverse DNS lookup using local resolver (NetBIOS/mDNS/LLMNR/DNS).
  - Can block if not timed out properly. To avoid stalling the scan completion, hostname lookups should either use a strict socket timeout (`socket.setdefaulttimeout(...)`) or concurrent resolution with thread pooling (`concurrent.futures.ThreadPoolExecutor`).
  - Must catch `(socket.herror, socket.gaierror, socket.timeout, OSError)` and return `None` gracefully if unresolvable.

### 1.3 MAC OUI Manufacturer Lookup
- A MAC address consists of 6 bytes (`XX:XX:XX:YY:YY:YY`). The first 3 bytes (`XX:XX:XX`) form the Organizationally Unique Identifier (OUI) assigned by IEEE.
- **Approach**:
  - Bundling a lightweight local dictionary of the top common vendor OUIs (Apple, Samsung, Intel, Cisco, Raspberry Pi, TP-Link, Google, Amazon, Microsoft, Dell, HP, etc.) guarantees fast, 100% offline lookup without external API calls or latency.
  - Normalization: Format MAC to uppercase without separators or with standard colons (`AA:BB:CC`).
  - Fallback: Return `"Unknown"` or `None` if OUI is not in the local database.

### 1.4 Scan Timing & Non-Blocking Design
- Measure elapsed time using `time.perf_counter()`.
- Record scan start time, finish time, and duration in seconds.
- Provide configurable timeout parameter (defaulting to `2.0` seconds from `config.SCAN_TIMEOUT`).

### 1.5 Testing & Mocking Strategy
- Scapy's `srp()` must be mocked in automated tests to allow continuous testing in restricted/CI environments without Npcap or live LAN adapters.
- Mock returning `(ans, unans)` pairs:
  ```python
  mock_answered = [(sent_packet, received_packet)]
  received_packet[ARP].psrc = "192.168.1.10"
  received_packet[ARP].hwsrc = "00:11:22:33:44:55"
  ```
- Test timeout behavior, empty responses, permission exceptions, and hostname resolution timeouts.
