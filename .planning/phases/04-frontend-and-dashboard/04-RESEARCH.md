# Phase 4 Research: Frontend and Dashboard Development

## 1. Design Direction & UX Principles

### 1.1 Aesthetic & Visual Identity
- NetScope is an engineer's network utility tool, not a generic consumer SaaS landing page.
- Typography: Clean sans-serif system font stack for UI controls and headers (`system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`), with tabular monospaced font (`Consolas, 'Courier New', monospace`) for all IP addresses, MAC addresses, CIDR blocks, and subnet masks to guarantee vertical alignment.
- Color Palette:
  - Base: High-contrast, clean slate aesthetic (slate-50 to slate-900).
  - Accents: Subtle steel blue / indigo (`#2563eb` / `#1d4ed8`) for active states and primary scan actions.
  - Status Indicators: Emerald/green (`#10b981`) for online/active, amber (`#f59e0b`) for scanning, rose/red (`#ef4444`) for errors/offline.
  - Avoid gimmicks: No heavy gradients, no blurry glassmorphism, no distracting animated canvas backgrounds.

### 1.2 Layout & Grid
- **Header Bar**: Brand logo + application name, live system status pill (e.g. `Idle`, `Scanning...`, `Error`).
- **Network Overview Banner**: 4-column metric grid displaying:
  1. Active Adapter (e.g. `Wi-Fi` / `Ethernet`).
  2. Local IPv4 & Netmask.
  3. Default Gateway.
  4. Network CIDR Target.
- **Action & Statistics Bar**:
  - Primary "Scan Network" button with spinner.
  - Metrics cards: Total Devices Discovered, Active Subnet, Last Scan Duration.
- **Controls Bar**:
  - Live search input (fuzzy/substring match across IP, MAC, Hostname, Manufacturer).
  - Status filter dropdown (`All Statuses`, `Online`, `Offline`).
- **Device Inventory Table**:
  - Columns: IP Address, MAC Address, Hostname, Manufacturer, Status, Discovered At.
  - Sorting & filtering in pure JavaScript without page reloads.
  - Clear empty states ("No devices discovered yet. Click 'Scan Network' to discover devices.") and error alerts.

## 2. Client-Side Architecture (Vanilla JavaScript)

### 2.1 State Management in `static/js/app.js`
- Pure client-side state object:
  ```javascript
  const state = {
    network: null,
    devices: [],
    filteredDevices: [],
    isScanning: false,
    status: 'idle',
    searchQuery: '',
    statusFilter: 'all',
    pollInterval: null,
  };
  ```

### 2.2 Polling & Lifecycle Flow
```
[User clicks "Scan Network"]
        │
        ▼
POST /api/scan  ─────────► Server returns 202 Accepted (or 409 if busy)
        │
        ├──► Disable "Scan" button, show spinner, set state to 'scanning'
        │
        ▼
Start Polling (GET /api/status every 800ms)
        │
        ├──────► Still 'scanning' ──► Keep spinner active
        │
        └──────► 'completed' or 'error'
                     │
                     ├──► Stop polling interval
                     ├──► Re-enable "Scan" button
                     ├──► Fetch latest devices: GET /api/devices
                     └──► Render table & metrics
```

### 2.3 Resilient Error & Disconnection Handling
- All `fetch()` calls wrapped in `try/catch`.
- If server is unreachable (e.g. backend stopped or restarted), display an unobtrusive top warning banner rather than throwing unhandled exceptions.
