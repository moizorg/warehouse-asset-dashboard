import os
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS
from .database import Database
from .routes.assets import assets_bp


def create_app(test_config=None):
    app = Flask(__name__)
    backend_root = Path(__file__).resolve().parent.parent
    default_database = backend_root / "data" / "assets.db"
    turso_database = os.getenv("TURSO_DATABASE_URL")
    database_path = turso_database or os.getenv("DATABASE_PATH", str(default_database))
    default_upload_folder = backend_root / "uploads"
    app.config.update(
        TESTING=False,
        DATABASE=database_path,
        UPLOAD_FOLDER=os.getenv("UPLOAD_FOLDER", str(default_upload_folder)),
        MAX_CONTENT_LENGTH=5 * 1024 * 1024,
        ALLOWED_ORIGINS=os.getenv(
            "ALLOWED_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(","),
    )
    if test_config:
        app.config.update(test_config)

    CORS(
        app,
        resources={r"/api/*": {"origins": app.config["ALLOWED_ORIGINS"]}},
    )

    database = Database(app.config["DATABASE"])
    app.extensions["database"] = database
    database.initialize()

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    app.register_blueprint(assets_bp)

    @app.errorhandler(413)
    def request_too_large(error):
        return jsonify(error="File must be 5 MB or smaller."), 413

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(error="The requested resource was not found."), 404

    return app
