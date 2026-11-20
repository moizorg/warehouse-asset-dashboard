from pathlib import Path
import shutil
from app import create_app


app = create_app()

photo_dir = Path(__file__).resolve().parent / "seed_assets"

category_photos = {
    "Machinery": "machinery.jpg",
    "Tools": "tools.jpg",
    "Electronics": "electronics.jpg",
    "Furniture": "furniture.jpg",
    "Vehicles": "vehicles.jpg",
    "Safety Equipment": "safety.jpg",
    "Other": "warehouse.jpg",
}

samples = []
category_names = list(category_photos)
for index in range(1, 29):
    category = category_names[(index - 1) % len(category_names)]
    prefix = {
        "Machinery": "MCH",
        "Tools": "TLS",
        "Electronics": "ELC",
        "Furniture": "FRN",
        "Vehicles": "VHC",
        "Safety Equipment": "SFT",
        "Other": "OTH",
    }[category]
    samples.append((f"WH-{prefix}-{index:03d}", category))

with app.app_context():
    database = app.extensions["database"]
    upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
    upload_folder.mkdir(parents=True, exist_ok=True)

    for identifier, category in samples:
        filename = f"sample-{identifier.lower().replace('/', '-')}.jpg"
        source_photo = photo_dir / category_photos[category]
        shutil.copyfile(source_photo, upload_folder / filename)
        photograph_path = f"uploads/{filename}"

        with database.connect() as connection:
            existing = connection.execute(
                "SELECT id FROM assets WHERE asset_identifier = ?", (identifier,)
            ).fetchone()
        if existing:
            with database.connect() as connection:
                connection.execute(
                    "UPDATE assets SET photograph_path = ?, category = ? WHERE id = ?",
                    (photograph_path, category, existing["id"]),
                )
            continue

        with database.connect() as connection:
            connection.execute(
                """
                INSERT INTO assets (asset_identifier, category, photograph_path, created_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (identifier, category, photograph_path),
            )

print("Seed data initialized.")
