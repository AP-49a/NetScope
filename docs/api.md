# NetScope — REST API Reference

NetScope exposes a local RESTful JSON API bound to `127.0.0.1:5000`.

---

## Base URL
```
http://127.0.0.1:5000/api
```

---

## 1. Network Information

### `GET /api/network`
Retrieves network details for the active primary interface on the host machine.

#### Request
- **Method:** `GET`
- **Headers:** `Accept: application/json`

#### Response (`200 OK`)
```json
{
  "interface_name": "Wi-Fi",
  "ip_address": "192.168.1.50",
  "subnet_mask": "255.255.255.0",
  "gateway": "192.168.1.1",
  "cidr": "192.168.1.0/24"
}
```

#### Error Response (`404 Not Found`)
```json
{
  "error": "No active network interface found"
}
```

---

## 2. Trigger Scan

### `POST /api/scan`
Initiates an asynchronous ARP sweep across the target CIDR range. If no CIDR is specified, the active subnet CIDR is automatically resolved.

#### Request
- **Method:** `POST`
- **Headers:** `Content-Type: application/json`
- **Body Parameters (Optional):**
  - `cidr` (*string*): Target subnet in valid CIDR notation (e.g. `"192.168.1.0/24"`).
  - `timeout` (*number*): Scan duration timeout in seconds (default `2.0`, must be `> 0`).

```json
{
  "cidr": "192.168.1.0/24",
  "timeout": 2.0
}
```

#### Response (`202 Accepted`)
```json
{
  "message": "Scan initiated",
  "status": "scanning",
  "cidr": "192.168.1.0/24"
}
```

#### Error Responses
- **`400 Bad Request`** (Invalid or malformed parameters):
  ```json
  {
    "error": "Invalid CIDR network format: 999.999.0.0/24"
  }
  ```
- **`409 Conflict`** (Scan already running):
  ```json
  {
    "error": "Scan already in progress",
    "status": "scanning"
  }
  ```

---

## 3. Scanner Status

### `GET /api/status`
Returns the real-time operational status and metrics of the scanning service.

#### Request
- **Method:** `GET`

#### Response (`200 OK`)
```json
{
  "status": "completed",
  "is_scanning": false,
  "started_at": "2026-11-11T12:00:00Z",
  "completed_at": "2026-11-11T12:00:02Z",
  "duration_seconds": 2.14,
  "device_count": 8,
  "error": null
}
```

Possible `status` values:
- `"idle"`: Scanner ready, no active scan running.
- `"scanning"`: Background ARP sweep in progress.
- `"completed"`: Last scan finished successfully.
- `"error"`: Last scan failed (details in `error` field).

---

## 4. Device Inventory

### `GET /api/devices`
Retrieves all discovered network devices from the persistent SQLite database.

#### Request
- **Method:** `GET`
- **Query Parameters (Optional):**
  - `status` (*string*): Filter by device status (`"online"` or `"offline"`). Default returns all.

#### Response (`200 OK`)
```json
{
  "count": 2,
  "devices": [
    {
      "id": 1,
      "mac_address": "00:17:F2:12:34:56",
      "ip_address": "192.168.1.5",
      "hostname": "macbook.local",
      "manufacturer": "Apple",
      "first_seen": "2026-11-11 12:00:00",
      "last_seen": "2026-11-11 12:30:00",
      "status": "online"
    },
    {
      "id": 2,
      "mac_address": "00:07:AB:AA:BB:CC",
      "ip_address": "192.168.1.42",
      "hostname": "galaxy-phone",
      "manufacturer": "Samsung",
      "first_seen": "2026-11-11 10:15:00",
      "last_seen": "2026-11-11 11:00:00",
      "status": "offline"
    }
  ]
}
```

---

## 5. Scan History

### `GET /api/history`
Returns an audit log of previous scan sessions.

#### Request
- **Method:** `GET`
- **Query Parameters (Optional):**
  - `limit` (*integer*): Max sessions to return (default: 50).

#### Response (`200 OK`)
```json
{
  "count": 1,
  "history": [
    {
      "id": 1,
      "cidr": "192.168.1.0/24",
      "started_at": "2026-11-11 12:00:00",
      "completed_at": "2026-11-11 12:00:02",
      "duration_seconds": 2.14,
      "devices_found": 8,
      "status": "completed",
      "error_message": null
    }
  ]
}
```
