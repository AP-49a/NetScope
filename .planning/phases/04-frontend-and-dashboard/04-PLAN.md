# Phase 4 Plan: Frontend and Dashboard Development

## Phase Objective
Build an intuitive, responsive, professional web dashboard for NetScope using clean HTML5, CSS3, and Vanilla JavaScript. The frontend connects to the Phase 3 REST APIs to display live network configuration, trigger background ARP scans with visual progress feedback, and provide a real-time searchable/filterable device inventory table.

**Phase Directory:** `.planning/phases/04-frontend-and-dashboard`  
**Status:** **Ready for Execution**  

---

## 1. Architectural Scope & Guardrails

```
┌─────────────────────────────────────────────────────────────┐
│                       In Scope (Phase 4)                    │
├─────────────────────────────────────────────────────────────┤
│ • templates/index.html semantic structure                   │
│ • static/css/style.css professional utility-focused design  │
│ • static/js/app.js state-driven async client application    │
│ • Live network overview cards (adapter, IP, mask, gateway)  │
│ • Scan action button with status polling & spinner          │
│ • Device table with IP, MAC, hostname, vendor, status       │
│ • Real-time search filter (IP, MAC, hostname, manufacturer) │
│ • Disconnection & error banner handling                     │
│ • Responsive design across desktop and mobile screens       │
│ • Automated frontend delivery tests (tests/test_frontend.py)│
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Locked Out (Phase 5+)                    │
├─────────────────────────────────────────────────────────────┤
│ ✕ SQLite database persistence (Phase 5)                     │
│ ✕ Device discovery history across browser reloads (Phase 5) │
│ ✕ Multi-scan historical comparison views (Phase 5)          │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Dashboard Components & Specifications

### 2.1 Navigation & System Banner
- **Branding**: NetScope wordmark with status badge (`Idle`, `Scanning...`, `Error`).
- **Connection Indicator**: Warning banner if API requests fail or server disconnects.

### 2.2 Network Overview Card Grid
- Displays live data from `GET /api/network`:
  1. **Interface**: e.g. `Wi-Fi (Active)` or `Ethernet (Active)`.
  2. **Local IP Address**: e.g. `192.168.1.15`.
  3. **Subnet Mask**: e.g. `255.255.255.0` (`/24`).
  4. **Gateway**: e.g. `192.168.1.1`.

### 2.3 Action Controls & Metrics Header
- **"Scan Network" Button**:
  - Triggers `POST /api/scan`.
  - Disables itself and displays animated spinner while `status === 'scanning'`.
- **Metrics Chips**:
  - Total Discovered Count.
  - Active Subnet CIDR.
  - Last Scan Duration (seconds).

### 2.4 Device Inventory Table & Search Filter
- **Controls**:
  - Live Search Box: Filter by substring in IP, MAC, Hostname, or Vendor.
  - Filter Select: Filter by status (`All`, `Online`).
- **Table Columns**:
  - `IP Address` (Monospace font)
  - `MAC Address` (Monospace font)
  - `Hostname` (Clean badge or italic `Unresolved`)
  - `Manufacturer` (Hardware vendor badge or `Unknown`)
  - `Status` (Pill badge: `Online`)
- **Empty State**: Clear placeholder when no scan has been executed yet.

---

## 3. Work Breakdown & Task Decomposition

### Wave 1: HTML Markup & Styling
* **Task 4.1: Dashboard Semantic HTML Shell**
  * **File:** `templates/index.html`
  * **Scope:**
    * Clean HTML5 layout with accessibility tags (`aria-live`, `aria-label`).
    * Navigation header, network info card grid, scan action bar, device inventory table, and modal/banner error containers.
  * **Verification:** Valid semantic structure without broken tag nesting.

* **Task 4.2: Utility-First Responsive Stylesheet**
  * **File:** `static/css/style.css`
  * **Scope:**
    * Dark-mode slate palette (`#0f172a`, `#1e293b`, `#334155`, text `#f8fafc`).
    * Monospace formatting for networking primitives (`code`, `td.mono`).
    * Responsive CSS grid & flexbox layout with mobile breakpoints (`@media (max-width: 768px)`).
    * Restrained animations (subtle button active states, loading spinner).
  * **Verification:** Clean visual hierarchy, zero overflowing elements on narrow viewports.

### Wave 2: Client Logic & API Integration
* **Task 4.3: Vanilla JavaScript Application Controller**
  * **File:** `static/js/app.js`
  * **Scope:**
    * Module-scoped state store (`state = { network, devices, isScanning, ... }`).
    * `fetchNetworkInfo()`: calls `GET /api/network` on initial load.
    * `triggerScan()`: sends `POST /api/scan`, initiates polling loop.
    * `pollStatus()`: calls `GET /api/status` at 800ms intervals until scan completion.
    * `fetchDevices()`: calls `GET /api/devices` to update table.
    * Search & filter event listeners: re-filters `state.devices` without network calls.
    * Render functions: `renderNetwork()`, `renderMetrics()`, `renderTable()`, `renderStatusBadge()`.
  * **Verification:** Browser loads dashboard, initiates scans, updates DOM live.

### Wave 3: Testing & Verification
* **Task 4.4: Automated Frontend Delivery Tests**
  * **File:** `tests/test_frontend.py`
  * **Scope:**
    * Verifies `GET /` serves HTML containing required element IDs (`#network-cards`, `#scan-btn`, `#devices-table`, `#search-input`).
    * Verifies `static/css/style.css` and `static/js/app.js` are served with 200 OK and appropriate content types.
    * Verifies template handles empty/missing network configurations cleanly.
  * **Verification:** `python -m pytest tests/test_frontend.py -v` passes 100%.

* **Task 4.5: Documentation & Milestone Updates**
  * **Files:** `README.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`
  * **Scope:** Update roadmap, provide screenshot guidance and UI documentation.

---

## 4. Acceptance Criteria Checklist

- [ ] Dashboard HTML loads with complete UI components.
- [ ] Network overview cards populate with live data from `GET /api/network`.
- [ ] Clicking "Scan Network" dispatches `POST /api/scan` and disables button.
- [ ] Scanning state triggers visual spinner and status badge update.
- [ ] Discovered devices populate into the inventory table when scan finishes.
- [ ] Real-time search filters table rows by IP, MAC, hostname, and vendor.
- [ ] Empty state is displayed when no devices are present.
- [ ] Disconnection or server error renders clean feedback banner.
- [ ] All new tests in `tests/test_frontend.py` pass.
- [ ] All 101 existing Phase 1, 2, and 3 tests continue to pass without regression.
