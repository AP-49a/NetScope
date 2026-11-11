"""
app.py — NetScope Flask application entry point.

Phase 1: Stub only.
Phase 2: Flask app factory, blueprint registration, and dev-server launch
         will be implemented here.
"""

from __future__ import annotations

# ── Phase 2 implementation outline ──────────────────────────────────────────
#
# from flask import Flask
# from flask_cors import CORS
# from config import FLASK_HOST, FLASK_PORT, FLASK_DEBUG, SECRET_KEY
# from api.routes import api_bp
# from utils.logger import configure_logging, get_logger
# from config import LOG_LEVEL, LOG_FILE
#
# def create_app() -> Flask:
#     configure_logging(log_level=LOG_LEVEL, log_file=LOG_FILE)
#     logger = get_logger(__name__)
#
#     app = Flask(__name__, template_folder="templates", static_folder="static")
#     app.secret_key = SECRET_KEY
#     CORS(app)
#     app.register_blueprint(api_bp)
#
#     logger.info("NetScope application created.")
#     return app
#
# if __name__ == "__main__":
#     application = create_app()
#     application.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(
        "NetScope app.py — Phase 2 not yet implemented.\n"
        "Run the Phase 1 network detection demo with:\n"
        "  python -c \"from scanner.network import get_network_config; "
        "print(get_network_config())\""
    )
