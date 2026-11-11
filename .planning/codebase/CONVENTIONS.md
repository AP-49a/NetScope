# NetScope — Coding Conventions & Standards

## 1. Code Style & Formats

- **Language Standard**: Python 3.11+ syntax.
- **Future Annotations**: All Python source files must begin with `from __future__ import annotations` as the initial import to allow postponed evaluation of type annotations.
- **PEP 8 Compliance**: Strict adherence to PEP 8 whitespace, variable naming, line length (recommended max 88-100 characters), and structure.
- **Path Manipulation**: Mandatory usage of `pathlib.Path` instead of `os.path` operations.
- **Docstrings**: NumPy / Google style structured docstrings detailing module scope, parameters, return types, and exceptions.

## 2. Naming Conventions

- **Modules & Packages**: Lowercase with underscores if necessary (`interface.py`, `network.py`, `logger.py`).
- **Classes**: PascalCase (`InterfaceInfo`, `NetworkConfig`, `InterfaceKind`).
- **Enums**: PascalCase class, UPPER_SNAKE_CASE members (`InterfaceKind.ETHERNET`, `InterfaceKind.WIFI`).
- **Functions & Methods**: snake_case with clear verb-first names (`get_network_config()`, `list_interfaces()`, `calculate_cidr()`).
- **Constants & Configuration Variables**: UPPER_SNAKE_CASE (`FLASK_PORT`, `BASE_DIR`, `LOG_MAX_BYTES`).
- **Private / Internal Functions**: Prefixed with a single underscore (`_classify_interface()`, `_get_gateway_windows()`).

## 3. Typing Standards

- **Type Annotations**: Comprehensive type annotations on all function signatures, return values, and class attributes.
- **Optional Values**: Explicit `Optional[T]` or `T | None` for attributes that may be unassigned.
- **Data Models**: Use `@dataclass` for lightweight data holders (`InterfaceInfo`, `NetworkConfig`) instead of raw dictionaries or untyped tuples.

## 4. Error Handling & Robustness

- **Defensive Design**: Network detection must never crash the host process. Functions return `None` or structured objects with `None` fields when network information is unavailable.
- **Subprocess Isolation**: Subprocess calls (e.g., `route print`) must wrap specific exceptions:
  ```python
  try:
      result = subprocess.run(..., timeout=5)
  except (FileNotFoundError, subprocess.TimeoutExpired, OSError) as exc:
      logger.warning("Subprocess execution failed: %s", exc)
      return None
  ```
- **Logging vs Silent Failures**: All caught exceptions must be logged with contextual details at `DEBUG`, `WARNING`, or `ERROR` levels. Never use bare `except:` or suppress exceptions silently without documentation.

## 5. Logging Guidelines

- **Logger Acquisition**: Always acquire named loggers via `utils.logger.get_logger(__name__)`.
- **Log Levels**:
  - `DEBUG`: Fine-grained operational tracing (regex matches, individual interface evaluations).
  - `INFO`: Normal operational milestones (enumerated count, chosen active interface, server startup).
  - `WARNING`: Recoverable anomalies (missing gateway, fallback to console logger, unrecognised interface kind).
  - `ERROR`: Major subsystem failures (psutil enumeration failure, invalid network parameters).
- **Sensitive Data**: Avoid logging raw packet payloads or sensitive user credentials.
