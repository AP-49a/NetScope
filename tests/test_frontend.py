"""
tests/test_frontend.py — Frontend delivery and template rendering tests.

Verifies:
  - Dashboard HTML shell is served on GET / with 200 OK.
  - Required DOM landmarks and UI IDs are present in the rendered HTML.
  - Static CSS stylesheet is accessible and served with text/css MIME type.
  - Static JavaScript client script is accessible and served with javascript MIME type.
"""

from __future__ import annotations

from typing import Generator

import pytest
from flask.testing import FlaskClient

from app import create_app


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Test client fixture with TESTING mode active."""
    app = create_app({"TESTING": True})
    with app.test_client() as test_client:
        yield test_client


class TestFrontendDelivery:
    """Tests for dashboard HTML template and static assets."""

    def test_dashboard_html_served(self, client: FlaskClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.content_type
        html = response.get_data(as_text=True)

        # Essential layout elements
        assert "<title>NetScope" in html
        assert 'id="status-badge"' in html
        assert 'id="network-overview"' in html
        assert 'id="adapter-name"' in html
        assert 'id="local-ip"' in html
        assert 'id="subnet-mask"' in html
        assert 'id="gateway-ip"' in html

        # Scan controls and metrics
        assert 'id="scan-btn"' in html
        assert 'id="stat-device-count"' in html
        assert 'id="stat-cidr"' in html
        assert 'id="stat-duration"' in html

        # Filter & table components
        assert 'id="search-input"' in html
        assert 'id="status-filter"' in html
        assert 'id="devices-table"' in html
        assert 'id="devices-tbody"' in html
        assert 'id="table-empty"' in html

    def test_stylesheet_served(self, client: FlaskClient) -> None:
        response = client.get("/static/css/style.css")
        assert response.status_code == 200
        assert "text/css" in response.content_type
        css = response.get_data(as_text=True)
        assert "--bg-primary" in css
        assert ".data-table" in css

    def test_javascript_served(self, client: FlaskClient) -> None:
        response = client.get("/static/js/app.js")
        assert response.status_code == 200
        assert "javascript" in response.content_type
        js = response.get_data(as_text=True)
        assert "loadNetworkConfig" in js
        assert "onScanClick" in js
        assert "loadDevices" in js
