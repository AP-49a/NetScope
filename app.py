"""
app.py — NetScope Flask application factory and server entry point.

Initializes the Flask WSGI server, configures CORS, mounts the REST API Blueprint,
and serves the web application dashboard.
"""

from __future__ import annotations

from typing import Any, Optional

from flask import Flask
from flask_cors import CORS

from api.routes import api_bp
from config import (
    FLASK_DEBUG,
    FLASK_HOST,
    FLASK_PORT,
    LOG_FILE,
    LOG_LEVEL,
    SECRET_KEY,
    STATIC_DIR,
    TEMPLATES_DIR,
)
from utils.logger import configure_logging, get_logger

logger = get_logger(__name__)


def create_app(config_override: Optional[dict[str, Any]] = None) -> Flask:
    """
    Construct and configure the NetScope Flask application.

    Parameters
    ----------
    config_override : Optional[dict[str, Any]]
        Optional key-value overrides for test or staging configurations.

    Returns
    -------
    Flask
        Configured WSGI application instance.
    """
    configure_logging(log_level=LOG_LEVEL, log_file=LOG_FILE)

    app = Flask(
        __name__,
        template_folder=str(TEMPLATES_DIR),
        static_folder=str(STATIC_DIR),
    )

    app.secret_key = SECRET_KEY

    # Enable Cross-Origin Resource Sharing for API routes
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Apply configuration overrides if provided (e.g. TESTING=True)
    if config_override:
        app.config.update(config_override)

    # Register API and dashboard routes
    app.register_blueprint(api_bp)

    logger.info("NetScope Flask application initialized successfully.")
    return app


if __name__ == "__main__":
    application = create_app()
    logger.info("Starting NetScope web server on %s:%d", FLASK_HOST, FLASK_PORT)
    application.run(
        host=FLASK_HOST,
        port=FLASK_PORT,
        debug=FLASK_DEBUG,
    )
