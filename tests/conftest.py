"""
tests/conftest.py — pytest configuration for NetScope tests.

Configures logging for the test session, directing log output to a
temporary directory so tests run without requiring write access to logs/.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from utils.logger import configure_logging


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging(tmp_path_factory: pytest.TempPathFactory) -> None:
    """
    Set up logging for the full test session.

    Uses a temporary directory so the test suite never requires write
    access to the project's logs/ directory.
    """
    log_dir = tmp_path_factory.mktemp("logs")
    log_file = log_dir / "netscope_test.log"
    configure_logging(log_level="DEBUG", log_file=log_file)
