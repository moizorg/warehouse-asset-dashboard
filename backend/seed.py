import io
from pathlib import Path
from PIL import Image
from app import create_app


app = create_app()

samples = [
    ("WH-MCH-001", "Machinery"),
    ("WH-TLS-014", "Tools"),
    ("WH-ELC-008", "Electronics"),
    ("WH-SFT-022", "Safety Equipment"),
]

with app.app_context():
    database = app.extensions["database"]
    upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
    upload_folder.mkdir(parents=True, exist_ok=True)

    for identifier, category in samples:
        with database.connect() as connection:
            existing = connection.execute(
                "SELECT id FROM assets WHERE asset_identifier = ?", (identifier,)
            ).fetchone()
        if existing:
            continue

        filename = f"sample-{identifier.lower().replace('/', '-')}.jpg"
        image = Image.new("RGB", (640, 480), (44, 62, 80))
        image.save(upload_folder / filename, "JPEG", quality=88)
        photograph_path = f"uploads/{filename}"

        with database.connect() as connection:
            connection.execute(
                """
                INSERT INTO assets (asset_identifier, category, photograph_path, created_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (identifier, category, photograph_path),
            )

print("Seed data initialized.")
