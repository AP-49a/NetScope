# Phase 7 Plan: Polish, Documentation and Release

## Phase Objective
Prepare NetScope for its first stable, production-quality release: provide seamless Windows 11 startup mechanisms with preflight diagnostics, finalize comprehensive end-user and developer documentation (Npcap setup, troubleshooting, REST API specifications), perform codebase hygiene and UI polish, and complete final end-to-end verification.

**Phase Directory:** `.planning/phases/07-polish-and-release`  
**Status:** **Ready for Execution**  

---

## 1. Architectural Scope & Guardrails

```
┌─────────────────────────────────────────────────────────────┐
│                       In Scope (Phase 7)                    │
├─────────────────────────────────────────────────────────────┤
│ • Preflight launcher (run.py & run.bat) with diagnostics     │
│ • Comprehensive product README.md with setup & API reference│
│ • Detailed Npcap installation & troubleshooting guide        │
│ • Architecture and API documentation in docs/               │
│ • Dashboard UI polish and branding consistency               │
│ • Code hygiene, unused code cleanup, .gitignore verification │
│ • Final test suite execution (100% pass, ≥90% coverage)     │
│ • Roadmap and State sign-off for v1.0.0 release              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               Explicitly Out of Scope (Post-MVP)            │
├─────────────────────────────────────────────────────────────┤
│ • Deep packet inspection, port scanning, vulnerability scan │
│ • Cloud synchronization, user auth, remote multi-user mgmt  │
│ • Active packet blocking or firewall manipulation           │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Work Breakdown & Task Decomposition

### Wave 1: Windows 11 Startup Automation & Preflight Diagnostics
* **Task 7.1: Preflight Diagnostic Launcher (`run.py` and `run.bat`)**
  * **File:** `run.py`, `run.bat`
  * **Scope:**
    * Create a self-contained preflight script `run.py`:
      - Verify Python runtime (>= 3.11).
      - Check required dependencies (`flask`, `psutil`, `scapy`).
      - Diagnostic check for Npcap / Scapy raw socket capabilities, printing warning if not elevated or Npcap missing.
      - Ensure database schema is initialized (`init_db()`).
      - Run Flask server with structured startup banner and clean console output.
    * Create `run.bat` for one-click startup on Windows.
  * **Verification:** Run `python run.py --help` or preflight check mode.

### Wave 2: Comprehensive Documentation & Knowledge Base
* **Task 7.2: Production README Overhaul**
  * **File:** `README.md`
  * **Scope:**
    * Update `README.md` to represent complete system capabilities:
      - Project overview and feature highlights.
      - Windows 11 prerequisites and Npcap installation instructions with direct links and configuration flags.
      - Quick start guide (venv, requirements, configuration).
      - Running instructions (interactive script, dev server, background service).
      - Comprehensive REST API reference (`/api/network`, `/api/scan`, `/api/status`, `/api/devices`, `/api/history`).
      - Extensive Troubleshooting guide (Npcap missing, Administrator permissions, Wi-Fi driver issues, firewall policies).
      - Known technical limitations (transparent disclosure: ARP segment boundaries, non-responsive firewalled devices).
* **Task 7.3: Synchronized Architecture & API Documentation**
  * **Files:** `docs/architecture.md`, `docs/api.md`
  * **Scope:**
    * Update `docs/architecture.md` with SQLite WAL mode, database schema, threading model, and OUI resolver.
    * Create `docs/api.md` detailing every endpoint with request/response JSON schemas.

### Wave 3: UI Polish, Error Messages & Code Hygiene
* **Task 7.4: Dashboard Polish & Branding Consistency**
  * **Files:** `templates/index.html`, `static/css/style.css`, `static/js/app.js`
  * **Scope:**
    * Ensure header branding, version string (`v1.0.0`), favicon/icon fallback, and clear feedback on empty states.
    * Ensure friendly, actionable error messages in the UI for common scanner conditions (e.g. "Npcap driver or Administrator rights required for packet capture").
* **Task 7.5: Codebase Cleanup & Repository Hygiene**
  * **Files:** `.gitignore`, root directory cleanup
  * **Scope:**
    * Ensure all temporary databases, logs, and coverage reports are ignored.
    * Verify imports across all modules and eliminate dead or commented-out code.

### Wave 4: Release Verification & Milestone Sign-Off
* **Task 7.6: End-to-End Test Suite Execution**
  * **Scope:** Run full test suite with coverage report (`pytest tests/ --cov`). Ensure 100% pass rate.
* **Task 7.7: Roadmap & State Closure**
  * **Files:** `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/phases/07-polish-and-release/07-VERIFICATION.md`
  * **Scope:** Record completion of Phase 7, marking all 7 project phases complete and NetScope v1.0.0 release-ready.

---

## 3. Acceptance Criteria Checklist

- [ ] `run.py` preflight launcher created with system diagnostics and clean startup banners.
- [ ] `run.bat` created for Windows 11 startup.
- [ ] Complete `README.md` rewritten with setup, Npcap guide, API reference, and troubleshooting.
- [ ] `docs/architecture.md` and `docs/api.md` updated to match live implementation.
- [ ] Dashboard displays consistent branding, version `v1.0.0`, and user-friendly error banners.
- [ ] Codebase cleaned of obsolete files; `.gitignore` verified.
- [ ] Entire test suite passes 100% (119+ tests) with ≥90% code coverage.
- [ ] All 7 phases in `ROADMAP.md` marked completed.
