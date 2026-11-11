# NetScope — Project Implementation Plan

**Project Name:** NetScope  
**Document Type:** Software Development Implementation Plan  
**Version:** 1.0  
**Target Environment:** Windows 11  
**Development Environment:** Antigravity + GSD  
**Project Stage:** Initial Development

---

# 1. Project Overview

## 1.1 Introduction

NetScope is a locally hosted network discovery and monitoring web application designed to identify and monitor devices connected to a local network.

The application will allow users to scan their authorized local network, discover connected devices, inspect available device information, and maintain a history of previously discovered devices.

NetScope aims to provide a simple, clean, and informative interface for understanding local network activity without requiring users to work directly with command-line networking tools.

## 1.2 Primary Objective

Develop a lightweight desktop-accessible web application that:

- Identifies the active network interface.
- Retrieves local network configuration.
- Discovers devices connected to the local network.
- Retrieves available IP and MAC addresses.
- Identifies hostnames and manufacturers where possible.
- Maintains device discovery history.
- Displays network information through an interactive dashboard.

## 1.3 Target Users

- Students learning computer networking.
- Beginner network administrators.
- Developers and technology enthusiasts.
- Users who want visibility into their own local network.

## 1.4 Application Type

NetScope will be a **locally hosted web application**, not a cloud-hosted website.

The application will run on the user's Windows computer through a local Flask server.

The user will access the dashboard through a browser:

`http://127.0.0.1:5000`

The backend will communicate with the local network through the computer's network interfaces.

No external server or cloud infrastructure is required for the MVP.

---

# 2. Technology Stack

The following technologies are selected for the initial implementation.

| Layer | Technology | Responsibility |
|---|---|---|
| Backend | Python | Core application logic |
| Web framework | Flask | Local server and REST API |
| Network discovery | Scapy | ARP-based network scanning |
| Packet capture support | Npcap | Windows packet capture support |
| Frontend | HTML5 | Dashboard structure |
| Styling | CSS3 | Dashboard design |
| Client-side logic | Vanilla JavaScript | API communication and interactions |
| Database | SQLite | Device and scan history |
| Testing | Pytest | Automated testing |
| Version control | Git | Source control |

### Technical Constraints

- Use Python 3.11 or later.
- Use type hints wherever practical.
- Follow PEP 8 conventions.
- Use `pathlib` for filesystem paths.
- Store configuration separately from application logic.
- Avoid unnecessary dependencies.
- Keep frontend and backend responsibilities separate.
- Do not introduce React, Node.js, or a frontend build system in the MVP.

---

# 3. System Architecture

NetScope will follow a modular architecture.

## 3.1 High-Level Architecture

Browser Dashboard  
↓  
Flask Application  
↓  
REST API  
↓  
Application Services  
↓  
Network Scanner / Database  
↓  
Local Network

## 3.2 Component Responsibilities

### Frontend

Responsible for:

- Displaying network information.
- Showing discovered devices.
- Triggering network scans.
- Displaying scan progress and status.
- Searching and filtering devices.
- Displaying scan statistics.
- Handling loading, empty, and error states.

### Flask Backend

Responsible for:

- Serving the frontend.
- Exposing REST API endpoints.
- Validating incoming requests.
- Coordinating network scans.
- Managing scan state.
- Retrieving device records.
- Communicating with the database.

### Network Scanner

Responsible for:

- Identifying network configuration.
- Identifying active network interfaces.
- Calculating network CIDR ranges.
- Performing ARP discovery.
- Collecting available device information.
- Handling scanning errors and timeouts.

### Database

Responsible for:

- Storing discovered devices.
- Tracking first-seen and last-seen timestamps.
- Maintaining scan history.
- Recording scan results.

---

# 4. Project Directory Structure

Create the complete project directory structure during Phase 1.

Do not implement all modules immediately. Each module should be implemented only when its designated development phase begins.

```text
NetScope/
│
├── app.py
├── config.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
│
├── scanner/
│   ├── __init__.py
│   ├── network.py
│   ├── interface.py
│   └── discovery.py
│
├── api/
│   ├── __init__.py
│   └── routes.py
│
├── services/
│   ├── __init__.py
│   └── scan_service.py
│
├── database/
│   ├── __init__.py
│   ├── db.py
│   └── models.py
│
├── utils/
│   └── logger.py
│
├── templates/
│   └── index.html
│
├── static/
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── app.js
│   └── assets/
│
├── tests/
│   ├── __init__.py
│   ├── test_network.py
│   ├── test_interface.py
│   ├── test_discovery.py
│   ├── test_api.py
│   └── test_database.py
│
├── logs/
│   └── .gitkeep
│
└── docs/
    ├── architecture.md
    └── development-roadmap.md
```

## 4.1 Module Responsibilities

| File | Responsibility |
|---|---|
| `app.py` | Flask application entry point |
| `config.py` | Application configuration |
| `scanner/network.py` | Local IP, subnet, gateway and CIDR detection |
| `scanner/interface.py` | Network interface identification |
| `scanner/discovery.py` | ARP-based device discovery |
| `api/routes.py` | REST API route definitions |
| `services/scan_service.py` | Scan orchestration and state management |
| `database/db.py` | Database connection and initialization |
| `database/models.py` | Database models and operations |
| `utils/logger.py` | Centralized logging |
| `templates/index.html` | Dashboard HTML |
| `static/css/style.css` | Dashboard styling |
| `static/js/app.js` | Frontend interactions and API calls |
| `tests/` | Automated tests |

---

# 5. Development Roadmap

Development must follow the seven phases below in order.

GSD should treat each phase as a separate implementation milestone.

Do not begin the next phase until the current phase has passed its acceptance criteria.

---

## PHASE 1 — Environment Setup and Network Fundamentals

**Objective:** Establish the development environment, project structure, and foundational network information utilities.

### Tasks

1. Inspect the existing project directory before modifying anything.
2. Initialize the Git repository if it does not already exist.
3. Create the Python virtual environment.
4. Install and configure the required dependencies.
5. Document Npcap installation requirements for Windows.
6. Create the complete project directory structure.
7. Configure centralized application logging.
8. Implement network interface enumeration.
9. Identify active network interfaces.
10. Retrieve local IPv4 address.
11. Retrieve subnet mask.
12. Retrieve default gateway.
13. Calculate the corresponding CIDR network.
14. Handle missing or unavailable network information.
15. Write unit tests using mocks where appropriate.
16. Create initial documentation.

### Expected Deliverables

- Functional Python environment.
- Complete directory structure.
- Dependency configuration.
- Network interface detection module.
- Network configuration detection module.
- Logging utility.
- Unit tests.
- README.
- Architecture documentation.
- Development roadmap.

### Acceptance Criteria

- Python environment works successfully.
- Flask and Scapy import successfully.
- Npcap installation requirements are documented.
- Active network interfaces can be identified.
- Local IP, subnet mask, gateway, and CIDR can be retrieved where available.
- Network detection handles unavailable interfaces gracefully.
- Automated tests pass.
- No actual device discovery or dashboard implementation is introduced yet.

---

## PHASE 2 — Core Network Scanning Engine

**Objective:** Build the core device discovery functionality.

### Tasks

1. Implement ARP-based network discovery using Scapy.
2. Use the detected local CIDR range as the scan target.
3. Send ARP requests to discover devices.
4. Collect responding devices.
5. Retrieve available IP addresses.
6. Retrieve MAC addresses.
7. Attempt hostname resolution.
8. Implement MAC OUI-based manufacturer lookup.
9. Handle devices that do not respond.
10. Implement configurable scan timeouts.
11. Measure scan duration.
12. Handle permission errors and unavailable interfaces.
13. Return standardized device records.

### Device Data Structure

Each discovered device should follow a consistent structure:

```json
{
  "ip_address": "192.168.1.10",
  "mac_address": "AA:BB:CC:DD:EE:FF",
  "hostname": "example-device",
  "manufacturer": "Example Manufacturer",
  "status": "online"
}
```

Fields that cannot be identified should be represented as `null` or an appropriate unavailable value.

### Acceptance Criteria

- Scanner discovers responding devices on the authorized local network.
- Each discovered device contains an IP and MAC address when available.
- Hostname and manufacturer lookups fail gracefully.
- Scan duration is recorded.
- Timeouts and permission errors are handled.
- Scanner can be tested independently of Flask.
- Unit tests cover successful and unsuccessful discovery cases.

---

## PHASE 3 — Backend and REST API Development

**Objective:** Connect the network scanner to a Flask application and expose its functionality through API endpoints.

### Tasks

1. Initialize the Flask application.
2. Configure application settings.
3. Register API routes.
4. Integrate the scanner with the backend.
5. Implement scan orchestration.
6. Prevent simultaneous scans from interfering with each other.
7. Implement scan-state tracking.
8. Add request validation.
9. Add structured JSON responses.
10. Implement consistent error responses.
11. Add API-level automated tests.

### API Specification

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/network` | Retrieve current network configuration |
| POST | `/api/scan` | Start a new network scan |
| GET | `/api/devices` | Retrieve discovered devices |
| GET | `/api/status` | Retrieve application and scan status |

### Expected API Behaviour

**GET /api/network**

Returns:

- Active interface.
- Local IPv4 address.
- Subnet mask.
- Gateway.
- CIDR.

**POST /api/scan**

Starts a scan and returns a scan identifier or equivalent status information.

A long-running scan should not unnecessarily block other API requests.

**GET /api/devices**

Returns the current discovered-device collection.

**GET /api/status**

Returns whether the application is idle, scanning, or has encountered an error.

### Acceptance Criteria

- Flask server starts successfully.
- All documented endpoints work.
- Responses use consistent JSON structures.
- Invalid requests are handled safely.
- Simultaneous scan requests are controlled.
- API tests pass.
- Scanner errors do not crash the server.

---

## PHASE 4 — Frontend and Dashboard Development

**Objective:** Build a clean, professional, responsive dashboard that communicates with the Flask backend.

### Design Direction

The dashboard should feel like a real network utility rather than a generic AI-generated admin template.

Design principles:

- Clean and professional.
- Modern but restrained.
- Strong visual hierarchy.
- Minimal unnecessary decoration.
- Consistent spacing and typography.
- Readable tables and statistics.
- Subtle transitions and hover effects.
- Responsive layout.
- Light-first appearance.

Avoid:

- Excessive gradients.
- Excessive glassmorphism.
- Overuse of emerald green.
- Excessive rounded cards.
- Unnecessary animations.
- Fake analytics and placeholder statistics.
- Decorative elements that reduce readability.

### Dashboard Components

**A. Navigation**

- NetScope branding.
- Dashboard navigation.
- Network Devices section.
- Scan History section, once supported.
- Settings section, only if meaningful functionality exists.

**B. Network Overview**

Display:

- Active interface.
- Local IP.
- Subnet.
- Default gateway.
- Current scan status.

**C. Statistics**

Display:

- Total discovered devices.
- Currently online devices.
- Newly discovered devices.
- Last scan duration.

**D. Device Inventory**

Table columns:

- IP Address.
- MAC Address.
- Hostname.
- Manufacturer.
- Status.
- Last Seen.

**E. Scan Controls**

- Start Scan button.
- Scanning indicator.
- Progress or status feedback.
- Last scan information.

**F. Search and Filters**

Allow users to:

- Search by IP.
- Search by MAC.
- Search by hostname.
- Search by manufacturer.
- Filter by device status.

### Frontend Behaviour

- Fetch network information from the backend.
- Trigger scans through the API.
- Refresh device information after scans.
- Display loading states.
- Display empty states.
- Display useful error messages.
- Prevent repeated accidental scan submissions.
- Handle backend disconnection gracefully.

### Acceptance Criteria

- Dashboard loads through the local Flask server.
- Network information is displayed using real API data.
- Scan button triggers a real scan.
- Discovered devices appear in the device table.
- Search and filtering work.
- Loading, empty, and error states are implemented.
- Layout works on desktop and smaller screens.
- No fake device information is displayed.

---

## PHASE 5 — Database and Device History

**Objective:** Add persistent storage so device information is not lost when the application restarts.

### Database

Use SQLite.

### Initial Data Models

**Devices**

- Device ID.
- IP address.
- MAC address.
- Hostname.
- Manufacturer.
- First seen.
- Last seen.
- Current status.

**ScanHistory**

- Scan ID.
- Start time.
- End time.
- Scan duration.
- Number of discovered devices.
- Scan status.

**ScanResults**

- Record ID.
- Scan ID.
- Device ID.

### Tasks

1. Configure SQLite.
2. Implement database initialization.
3. Create the database models.
4. Save discovered devices.
5. Update existing device records.
6. Preserve first-seen timestamps.
7. Update last-seen timestamps.
8. Record scan history.
9. Associate discovered devices with scan records.
10. Retrieve historical device information.
11. Integrate database operations with the backend.
12. Add database tests.

### Device Tracking Logic

- If a device is discovered for the first time, create a record.
- If a known device is discovered again, update its last-seen timestamp.
- If a previously known device is not discovered in a subsequent scan, mark it as not currently seen.
- Do not permanently delete devices merely because they fail to respond to one scan.

### Acceptance Criteria

- Device records persist across application restarts.
- First-seen timestamps remain unchanged.
- Last-seen timestamps update correctly.
- Scan history is stored.
- Historical devices can be retrieved.
- Database operations are tested.

---

## PHASE 6 — Testing and Quality Assurance

**Objective:** Verify that NetScope works reliably under normal and abnormal conditions.

### Testing Categories

**1. Unit Testing**

- Network configuration utilities.
- Interface detection.
- Scanner logic.
- Database operations.
- Service-layer logic.

**2. Integration Testing**

- Scanner and backend integration.
- Backend and database integration.
- API and frontend integration.

**3. API Testing**

- Valid requests.
- Invalid requests.
- Missing parameters.
- Scanner failures.
- Concurrent scan requests.

**4. Frontend Testing**

- Dashboard loading.
- Search and filtering.
- Scan controls.
- Error messages.
- Responsive layout.

**5. Network Testing**

- Normal Wi-Fi network.
- Ethernet network, where available.
- Network interface unavailable.
- Devices not responding.
- Network disconnected during scanning.
- Permission restrictions.

**6. Performance Testing**

- Scan duration.
- Large device lists.
- Repeated scans.
- API response times.
- Memory usage.

### Acceptance Criteria

- Automated tests pass.
- No critical application crashes.
- Error states are understandable.
- Database records remain consistent.
- Repeated scans work correctly.
- Application can recover from temporary network failures.

---

## PHASE 7 — Polish, Documentation and Release

**Objective:** Prepare NetScope for a usable first release.

### Tasks

1. Finalize dashboard branding.
2. Review the complete UI.
3. Improve error messages.
4. Remove unused code and dependencies.
5. Review security and configuration.
6. Improve application logging.
7. Finalize README documentation.
8. Add installation instructions.
9. Add Npcap setup instructions.
10. Add troubleshooting documentation.
11. Document API endpoints.
12. Prepare screenshots.
13. Verify clean installation.
14. Create a release version.

### Expected Deliverables

- Stable NetScope MVP.
- Complete README.
- Installation guide.
- Troubleshooting guide.
- Architecture documentation.
- API documentation.
- Requirements file.
- GitHub-ready repository.

### Acceptance Criteria

A user should be able to:

1. Install the prerequisites.
2. Set up the Python environment.
3. Start NetScope.
4. Open the dashboard in a browser.
5. View their network configuration.
6. Scan their authorized local network.
7. View discovered devices.
8. Search and filter devices.
9. Review previous device discoveries.
10. Restart the application without losing saved history.

---

# 6. Functional Requirements

The MVP must support the following capabilities.

| ID | Requirement | Priority |
|---|---|---|
| FR-01 | Detect active network interface | High |
| FR-02 | Retrieve local network configuration | High |
| FR-03 | Calculate local CIDR range | High |
| FR-04 | Perform ARP-based device discovery | High |
| FR-05 | Retrieve IP and MAC addresses | High |
| FR-06 | Attempt hostname resolution | Medium |
| FR-07 | Identify manufacturer using MAC OUI | Medium |
| FR-08 | Display discovered devices | High |
| FR-09 | Search and filter devices | Medium |
| FR-10 | Store device history | High |
| FR-11 | Maintain scan history | Medium |
| FR-12 | Display scan statistics | Medium |
| FR-13 | Handle scanner errors gracefully | High |

---

# 7. Non-Functional Requirements

### Performance

- Avoid unnecessarily blocking the Flask application during scans.
- Use configurable scanning timeouts.
- Keep the dashboard responsive.
- Avoid unnecessary repeated network requests.

### Reliability

- Handle unavailable network interfaces.
- Handle missing network configuration.
- Handle permission errors.
- Handle devices that do not respond.
- Preserve database consistency.

### Security

- Bind the local application to `127.0.0.1` by default.
- Do not expose the scanner to the public internet.
- Validate scan targets.
- Restrict scanning to authorized networks.
- Do not execute arbitrary commands from frontend input.
- Do not collect or transmit unnecessary personal information.

### Maintainability

- Maintain modular code.
- Separate API, services, scanner, and database responsibilities.
- Use clear function and variable names.
- Add useful comments where necessary.
- Keep documentation synchronized with implementation.

---

# 8. Important Technical Limitations

These limitations must be considered during development and documented accurately.

1. ARP discovery primarily identifies devices on the same local network segment.
2. Devices behind other routers generally cannot be discovered through the local ARP scan.
3. Devices may not respond because of firewall rules, network isolation, sleep states, or other restrictions.
4. MAC addresses may not be available for devices outside the local network segment.
5. Hostname resolution may fail.
6. MAC manufacturer identification depends on available OUI data.
7. Manufacturer information is not guaranteed to identify the actual device model.
8. Windows packet capture and some scanning operations may require Npcap and elevated permissions.
9. A device missing from one scan must not automatically be assumed to be permanently disconnected.

NetScope must display unavailable information honestly instead of inventing values.

---

# 9. GSD Development Instructions

This section is specifically intended for Antigravity and the GSD workflow.

## 9.1 Source of Truth

Treat this document as the primary product and implementation specification.

Before implementing anything:

1. Read this document completely.
2. Inspect the existing project and repository.
3. Review the current GSD project state.
4. Identify completed work and outstanding requirements.
5. Check existing architecture before proposing changes.
6. Avoid recreating already completed functionality.

## 9.2 Phase-Based Execution

Follow the seven phases in their specified order.

For each phase:

1. Review the phase objective.
2. Break the phase into manageable tasks.
3. Identify dependencies.
4. Implement incrementally.
5. Test each meaningful component.
6. Review the implementation.
7. Verify the phase acceptance criteria.
8. Update project documentation.
9. Record completed work and remaining issues.
10. Only then proceed to the next phase.

## 9.3 GSD Planning Behaviour

Use GSD to:

- Understand project requirements.
- Create a project roadmap.
- Break phases into executable plans.
- Track implementation progress.
- Maintain architectural decisions.
- Track technical limitations.
- Verify phase completion.

Do not ask GSD to implement the entire project in a single operation.

Use its planning and verification workflow to maintain clear boundaries between phases.

## 9.4 Implementation Rules

- Do not skip phases.
- Do not introduce features outside the MVP scope without approval.
- Do not replace the selected technology stack without a clear technical reason.
- Do not overwrite existing project files without inspecting them.
- Do not create fake API responses to simulate completed features.
- Do not mark tests as passing unless they have actually been executed.
- Do not claim a feature is complete when only its interface has been implemented.
- Prefer small, verifiable changes.
- Keep all implementation decisions documented.

## 9.5 Phase Completion Reporting

At the end of every phase, provide:

- Summary of implemented features.
- Files created or modified.
- Dependencies added or changed.
- Tests executed and their actual results.
- Known issues.
- Outstanding tasks.
- Acceptance criteria checklist.
- Recommendation on whether the next phase can begin.

---

# 10. MVP Scope Boundaries

The following features are explicitly outside the initial MVP.

Do not implement them during the seven planned phases unless separately approved.

- Deep packet inspection.
- Real-time traffic analysis.
- Bandwidth monitoring.
- Intrusion detection.
- Port scanning.
- Vulnerability assessment.
- Automated device blocking.
- Router configuration.
- Remote network monitoring.
- Cloud synchronization.
- User authentication and multi-user accounts.
- AI-powered network analysis.
- Mobile application.

These may be considered for future versions after the core MVP is stable.

---

# 11. Future Development Possibilities

Potential future releases:

### NetScope 1.1
- Improved device identification.
- Manual device labels.
- Export device inventory.
- Improved scan scheduling.

### NetScope 1.2
- Optional continuous monitoring.
- Device appearance and disappearance notifications.
- Enhanced historical statistics.

### NetScope 2.0
- Traffic monitoring.
- Port and service discovery.
- Advanced network diagnostics.
- More detailed device analysis.

These are future possibilities, not commitments for the MVP.

---

# 12. Final Project Definition

NetScope is a Windows-compatible, locally hosted network discovery and monitoring web application built with Python, Flask, Scapy, SQLite, HTML, CSS, and JavaScript.

Its primary purpose is to provide a simple and reliable way to discover devices on an authorized local network, inspect available device information, and maintain a history of network discoveries.

The first release prioritizes:

1. Reliable network information detection.
2. Accurate local device discovery.
3. Clean backend architecture.
4. A functional and professional dashboard.
5. Persistent device history.
6. Reliable error handling and testing.
7. Clear installation and usage documentation.

**Development Strategy:** Build a working, tested MVP incrementally through seven controlled phases. Prioritize correctness, maintainability, and a useful user experience over feature quantity.

**End of Document.**