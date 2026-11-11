# NetScope — Roadmap

## Project Goal
A Windows 11 desktop-accessible web application for local network discovery and device monitoring built with Python, Flask, Scapy, SQLite, and vanilla frontend technologies.

---

## Phases

### [x] Phase 1: Environment Setup & Network Fundamentals
- **Directory**: `.planning/phases/01-environment-and-network-fundamentals`
- **Goal**: Establish the Python 3.11+ environment, project structure, logging, interface enumeration via psutil, network CIDR calculation, and unit tests with mocks.
- **Status**: Completed / Documented

### [x] Phase 2: Core Network Scanning Engine
- **Directory**: `.planning/phases/02-network-scanning-engine`
- **Goal**: Implement Scapy ARP broadcast scanning on local CIDR, IP/MAC discovery, hostname resolution, MAC OUI lookup, and standardized device records.
- **Status**: Completed / Verified (32 new tests, 89 total passing)

### [x] Phase 3: Backend and REST API Development
- **Directory**: `.planning/phases/03-backend-and-rest-api`
- **Goal**: Initialize Flask application, register REST endpoints (`/api/network`, `/api/scan`, `/api/devices`, `/api/status`), scan coordination, and concurrency controls.
- **Status**: Completed / Verified (12 new tests, 101 total passing)

### [x] Phase 4: Frontend and Dashboard Development
- **Directory**: `.planning/phases/04-frontend-and-dashboard`
- **Goal**: Responsive dashboard (HTML5/CSS3/Vanilla JS), network overview card, scan trigger with live indicator, and searchable device inventory table.
- **Status**: Completed / Verified (3 new tests, 104 total passing)

### [x] Phase 5: Database and Device History
- **Directory**: `.planning/phases/05-database-and-history`
- **Goal**: SQLite persistence for devices, first/last seen tracking, and scan session history.
- **Status**: Completed / Verified (7 new tests, 111 total passing)

### [x] Phase 6: Testing and Quality Assurance
- **Directory**: `.planning/phases/06-testing-and-qa`
- **Goal**: End-to-end integration tests, network failure handling, permission constraints, and edge case resilience.
- **Status**: Completed / Verified (8 new tests, 119 total passing, 92% coverage)

### [x] Phase 7: Polish, Documentation and Release
- **Directory**: `.planning/phases/07-polish-and-release`
- **Goal**: Troubleshooting documentation, Npcap setup guides, performance verification, and release preparation.
- **Status**: Completed / Verified (Preflight launcher, README, docs/api.md, docs/architecture.md, 119 tests passing, v1.0.0 Release Ready)
