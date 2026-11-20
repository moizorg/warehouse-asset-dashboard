from flask import Blueprint, current_app, jsonify, request, send_from_directory
from sqlite3 import IntegrityError
from pathlib import Path
from ..models import Asset
from ..services import (
    save_image,
    allocate_preset,
    validate_asset_identifier,
    validate_category,
    ValidationError,
)

assets_bp = Blueprint("assets", __name__, url_prefix="/api")


def photograph_url(asset_id):
    return f"/api/assets/{asset_id}/photograph"


def row_to_asset(row):
    if not row:
        return None
    return Asset(
        id=row["id"],
        asset_identifier=row["asset_identifier"],
        category=row["category"],
        photograph_path=row["photograph_path"],
        created_at=row["created_at"],
    )


@assets_bp.post("/assets")
def create_asset():
    try:
        identifier = validate_asset_identifier(request.form.get("asset_identifier"))
        category = validate_category(request.form.get("category"))
    except ValidationError as error:
        return jsonify(error=str(error)), error.status

    database = current_app.extensions["database"]
    with database.connect() as connection:
        duplicate = connection.execute(
            "SELECT id FROM assets WHERE asset_identifier = ? COLLATE NOCASE",
            (identifier,),
        ).fetchone()
    if duplicate:
        return jsonify(error="An asset with this Asset ID already exists."), 409

    try:
        uploaded = request.files.get("photograph")
        if uploaded and uploaded.filename:
            photograph_path = save_image(
                uploaded,
                current_app.config["UPLOAD_FOLDER"],
            )
        else:
            photograph_path = allocate_preset(
                category,
                current_app.config["UPLOAD_FOLDER"],
                database,
            )
    except ValidationError as error:
        return jsonify(error=str(error)), error.status

    database = current_app.extensions["database"]
    try:
        with database.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO assets (asset_identifier, category, photograph_path, created_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (identifier, category, photograph_path),
            )
            asset_id = cursor.lastrowid
            row = connection.execute(
                "SELECT * FROM assets WHERE id = ?", (asset_id,)
            ).fetchone()
    except IntegrityError:
        return jsonify(error="An asset with this Asset ID already exists."), 409

    asset = row_to_asset(row)
    return jsonify(asset.to_dict(photograph_url(asset.id))), 201


@assets_bp.get("/assets")
def list_assets():
    search = (request.args.get("search") or "").strip()
    try:
        page = max(1, int(request.args.get("page", "1")))
        limit = min(100, max(1, int(request.args.get("limit", "10"))))
    except ValueError:
        return jsonify(error="Page and limit must be integers."), 400

    offset = (page - 1) * limit
    database = current_app.extensions["database"]
    with database.connect() as connection:
        if search:
            total = connection.execute(
                "SELECT COUNT(*) FROM assets WHERE asset_identifier LIKE ? COLLATE NOCASE",
                (f"%{search}%",),
            ).fetchone()[0]
            rows = connection.execute(
                """
                SELECT * FROM assets
                WHERE asset_identifier LIKE ? COLLATE NOCASE
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (f"%{search}%", limit, offset),
            ).fetchall()
        else:
            total = connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
            rows = connection.execute(
                """
                SELECT * FROM assets
                ORDER BY created_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()

    items = [
        row_to_asset(row).to_dict(photograph_url(row["id"]))
        for row in rows
    ]
    return jsonify(
        items=items,
        pagination={
            "page": page,
            "limit": limit,
            "total": total,
            "pages": max(1, (total + limit - 1) // limit),
        },
    )


@assets_bp.get("/assets/<int:asset_id>")
def get_asset(asset_id):
    database = current_app.extensions["database"]
    with database.connect() as connection:
        row = connection.execute(
            "SELECT * FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
    if not row:
        return jsonify(error="Asset not found."), 404
    asset = row_to_asset(row)
    return jsonify(asset.to_dict(photograph_url(asset.id)))


@assets_bp.get("/assets/<int:asset_id>/photograph")
def get_photograph(asset_id):
    database = current_app.extensions["database"]
    with database.connect() as connection:
        row = connection.execute(
            "SELECT photograph_path FROM assets WHERE id = ?", (asset_id,)
        ).fetchone()
    if not row:
        return jsonify(error="Asset not found."), 404

    relative_path = row["photograph_path"].replace("\\", "/")
    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()
    requested_path = (upload_root / relative_path.removeprefix("uploads/")).resolve()
    if upload_root not in requested_path.parents:
        return jsonify(error="Invalid photograph path."), 404
    relative_name = requested_path.relative_to(upload_root).as_posix()
    directory = upload_root / relative_name.rsplit("/", 1)[0]
    filename = requested_path.name
    return send_from_directory(
        str(directory),
        filename,
        as_attachment=False,
        max_age=0,
    )
