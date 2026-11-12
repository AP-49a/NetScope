"""
api/routes.py — Flask REST API route definitions.

Exposes REST endpoints for inspecting network configuration, triggering
background ARP scans, polling scan state, retrieving persistent devices,
and inspecting historical scan sessions.
"""

from __future__ import annotations

import ipaddress
from typing import Any

from flask import Blueprint, jsonify, render_template, request

from database.models import get_scan_history, set_device_custom_name
from scanner.network import get_network_config
from services.scan_service import scan_service
from utils.logger import get_logger

logger = get_logger(__name__)

api_bp = Blueprint("api", __name__)


# ---------------------------------------------------------------------------
# Dashboard Root Route
# ---------------------------------------------------------------------------


@api_bp.get("/")
def index() -> Any:
    """Serve the primary dashboard web application shell."""
    return render_template("index.html")


# ---------------------------------------------------------------------------
# REST API Endpoints
# ---------------------------------------------------------------------------


@api_bp.get("/api/network")
def get_network() -> Any:
    """
    Retrieve active network interface and IP configuration.

    Returns 200 OK with network details, or 500 if configuration resolution fails.
    """
    try:
        config = get_network_config()
        if not config:
            return (
                jsonify(
                    {
                        "error": "No active network interface found.",
                        "interface_name": None,
                        "ip_address": None,
                        "subnet_mask": None,
                        "gateway": None,
                        "cidr": None,
                        "is_complete": False,
                    }
                ),
                200,
            )

        return (
            jsonify(
                {
                    "interface_name": config.interface_name,
                    "ip_address": config.ip_address,
                    "subnet_mask": config.subnet_mask,
                    "gateway": config.gateway,
                    "cidr": config.cidr,
                    "prefix_length": config.prefix_length,
                    "is_complete": config.is_complete,
                }
            ),
            200,
        )
    except Exception as exc:
        logger.error("Error retrieving network config: %s", exc, exc_info=True)
        return jsonify({"error": f"Failed to retrieve network configuration: {exc}"}), 500


@api_bp.post("/api/scan")
def start_scan() -> Any:
    """
    Initiate an asynchronous ARP network scan.

    Accepts optional JSON payload with ``cidr``, ``interface``, and ``timeout``.
    Returns 202 Accepted if started, or 409 Conflict if already scanning.
    """
    payload = request.get_json(silent=True) or {}

    cidr = payload.get("cidr")
    interface = payload.get("interface")
    timeout = payload.get("timeout")

    if cidr is not None:
        if not isinstance(cidr, str) or not cidr.strip():
            return jsonify({"error": "CIDR target must be a non-empty string."}), 400
        try:
            ipaddress.ip_network(cidr.strip(), strict=False)
        except ValueError:
            return jsonify({"error": f"Invalid CIDR network format: '{cidr}'."}), 400

    if timeout is not None:
        try:
            timeout = float(timeout)
            if timeout <= 0:
                return jsonify({"error": "Timeout must be greater than 0 seconds."}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid timeout parameter: must be a numeric value."}), 400

    started, message = scan_service.start_scan(
        cidr=cidr,
        interface_name=interface,
        timeout=timeout,
    )

    if not started:
        return (
            jsonify(
                {
                    "error": message,
                    "status": "scanning",
                }
            ),
            409,
        )

    return (
        jsonify(
            {
                "message": message,
                "status": "scanning",
                "target_cidr": cidr or "auto",
            }
        ),
        202,
    )


@api_bp.get("/api/status")
def get_status() -> Any:
    """
    Retrieve current status of the network scanner and last scan summary.
    """
    status_data = scan_service.get_status()
    return jsonify(status_data), 200


@api_bp.get("/api/devices")
def get_devices() -> Any:
    """
    Retrieve persistent collection of discovered devices.

    Supports optional query parameter ``?status=online|offline``.
    """
    status_filter = request.args.get("status")
    devices = scan_service.get_devices(status_filter=status_filter)
    return (
        jsonify(
            {
                "count": len(devices),
                "devices": devices,
            }
        ),
        200,
    )


@api_bp.route("/api/devices/<mac>", methods=["PATCH"])
def update_device_name(mac: str) -> Any:
    """
    Update user-defined custom friendly name for a device.
    """
    data = request.get_json(silent=True) or {}
    custom_name = data.get("custom_name")

    success = set_device_custom_name(mac, custom_name)
    if not success:
        return jsonify({"error": f"Device with MAC '{mac}' not found."}), 404

    return (
        jsonify(
            {
                "message": "Device nickname updated successfully",
                "mac_address": mac.upper(),
                "custom_name": custom_name.strip() if custom_name and custom_name.strip() else None,
            }
        ),
        200,
    )


@api_bp.get("/api/history")
def get_history() -> Any:
    """
    Retrieve historical audit log of past scan sessions.

    Supports optional query parameter ``?limit=N`` (default: 20).
    """
    try:
        limit = int(request.args.get("limit", 20))
        limit = max(1, min(limit, 100))
    except ValueError:
        limit = 20

    history = get_scan_history(limit=limit)
    return (
        jsonify(
            {
                "count": len(history),
                "history": history,
            }
        ),
        200,
    )
