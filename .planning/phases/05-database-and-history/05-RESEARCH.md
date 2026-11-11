# Phase 5 Research: Database and Device History

## 1. Domain & Technology Research (SQLite 3 on Windows 11)

### 1.1 SQLite Configuration & Concurrency on Windows
- **Connection Model**: Python's built-in `sqlite3` module provides lightweight, zero-configuration local persistence.
- **WAL Mode (`PRAGMA journal_mode = WAL`)**:
  - Windows file locking can cause `sqlite3.OperationalError: database is locked` if a background scan thread writes while a Flask request thread reads.
  - Enabling WAL (Write-Ahead Logging) allows concurrent readers alongside a single writer without blocking.
- **Foreign Key Enforcement (`PRAGMA foreign_keys = ON`)**:
  - Must be explicitly enabled on every connection in SQLite.
- **Thread Safety**:
  - SQLite connections should not be shared across threads unless configured with `check_same_thread=False` or created per-thread / per-operation. Using a context manager (`with get_connection() as conn:`) ensures clean connection lifetime, automatic commit on success, and rollback on exception.

### 1.2 Schema Architecture

#### `devices` Table
Tracks all unique hardware observed over time across all network scans.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `mac_address`: TEXT NOT NULL UNIQUE (indexed)
- `ip_address`: TEXT NOT NULL (most recently observed IP)
- `hostname`: TEXT NULL (most recently resolved PTR / NetBIOS name)
- `manufacturer`: TEXT NULL (hardware vendor derived from OUI)
- `first_seen`: TEXT NOT NULL (ISO 8601 UTC timestamp of first discovery)
- `last_seen`: TEXT NOT NULL (ISO 8601 UTC timestamp of most recent reply)
- `status`: TEXT NOT NULL DEFAULT 'online' ('online' | 'offline')

#### `scan_history` Table
Audits every executed network scan session.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `cidr`: TEXT NOT NULL
- `interface_name`: TEXT NOT NULL
- `started_at`: TEXT NOT NULL
- `completed_at`: TEXT NOT NULL
- `duration_seconds`: REAL NOT NULL
- `device_count`: INTEGER NOT NULL DEFAULT 0
- `status`: TEXT NOT NULL ('completed' | 'error')
- `error_message`: TEXT NULL

#### `scan_results` Table (Join / Association)
Links which devices were observed in which specific scan run.
- `id`: INTEGER PRIMARY KEY AUTOINCREMENT
- `scan_id`: INTEGER NOT NULL (FK -> scan_history.id ON DELETE CASCADE)
- `device_id`: INTEGER NOT NULL (FK -> devices.id ON DELETE CASCADE)

### 1.3 Device Lifecycle & Tracking Logic
1. **New Device Discovery**:
   - Device MAC not found in `devices` table:
   - Insert new row with `first_seen = timestamp`, `last_seen = timestamp`, `status = "online"`.
2. **Existing Device Re-discovery**:
   - Device MAC already exists in `devices`:
   - Update `ip_address = new_ip`, `last_seen = timestamp`, `status = "online"`.
   - Update `hostname = new_hostname or existing_hostname` (never overwrite with `None` if previously known).
   - Update `manufacturer = new_vendor or existing_vendor`.
   - **Crucial**: `first_seen` must **never** be updated or overwritten.
3. **Missing Device State Transition**:
   - If a known device in the database fails to respond to a scan over its subnet, transition its status to `"offline"`.
   - Never permanently delete a device record due to a single missed scan.

### 1.4 Testability & Isolation
- Support passing an in-memory database (`":memory:"`) or temporary file path (`tmp_path / "test.db"`) to `init_db()` and data access functions.
- Unit tests can run hermetically without polluting `netscope.db`.
