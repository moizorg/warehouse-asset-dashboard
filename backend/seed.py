from pathlib import Path
from PIL import Image, ImageEnhance
from app import create_app


app = create_app()

photo_dir = Path(__file__).resolve().parent / "seed_assets"

samples = []
category_names = [
    "Machinery",
    "Tools",
    "Electronics",
    "Furniture",
    "Vehicles",
    "Safety Equipment",
]
category_photos = {
    "Machinery": "machinery.jpg",
    "Tools": "tools.jpg",
    "Electronics": "electronics.jpg",
    "Furniture": "furniture.jpg",
    "Vehicles": "vehicles.jpg",
    "Safety Equipment": "safety.jpg",
}
for index in range(1, 31):
    category = category_names[(index - 1) % len(category_names)]
    prefix = {
        "Machinery": "MCH",
        "Tools": "TLS",
        "Electronics": "ELC",
        "Furniture": "FRN",
        "Vehicles": "VHC",
        "Safety Equipment": "SFT",
    }[category]
    samples.append((f"WH-{prefix}-{index:03d}", category))

category_color_tints = {
    "Machinery": (232, 114, 62),
    "Tools": (226, 166, 74),
    "Electronics": (72, 142, 176),
    "Furniture": (205, 126, 82),
    "Vehicles": (112, 130, 150),
    "Safety Equipment": (224, 178, 52),
}

with app.app_context():
    database = app.extensions["database"]
    upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
    upload_folder.mkdir(parents=True, exist_ok=True)

    for old_photo in upload_folder.glob("sample-*.jpg"):
        old_photo.unlink()

    with database.connect() as connection:
        connection.execute("DELETE FROM assets")

    for identifier, category in samples:
        filename = f"sample-{identifier.lower().replace('/', '-')}.jpg"
        source_photo = photo_dir / category_photos[category]
        asset_number = int(identifier[-3:])
        with Image.open(source_photo).convert("RGB") as base:
            base = base.resize((960, 720))
            unique_image = base
            unique_image = ImageEnhance.Brightness(unique_image).enhance(
                0.82 + ((asset_number % 7) * 0.055)
            )
            unique_image = ImageEnhance.Contrast(unique_image).enhance(
                1.05 + ((asset_number % 5) * 0.07)
            )
            unique_image = ImageEnhance.Color(unique_image).enhance(
                0.82 + ((asset_number % 6) * 0.12)
            )
            tint = category_color_tints[category]
            tint_layer = Image.new("RGB", unique_image.size, tint)
            unique_image = Image.blend(
                unique_image,
                tint_layer,
                0.035 + ((asset_number % 4) * 0.012),
            )
            unique_image.save(upload_folder / filename, "JPEG", quality=88)
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
