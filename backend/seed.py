from pathlib import Path
from PIL import Image, ImageEnhance

from app import create_app


app = create_app()

CATEGORY_SOURCES = {
    "Electronics": "electronics.jpg",
    "Tools": "tools.jpg",
    "Machinery": "machinery.jpg",
    "Other": "warehouse.jpg",
    "Safety Equipment": "safety.jpg",
    "Vehicles": "vehicles.jpg",
    "Furniture": "furniture.jpg",
}

CATEGORY_PREFIXES = {
    "Electronics": "ELC",
    "Tools": "TLS",
    "Machinery": "MCH",
    "Other": "OTH",
    "Safety Equipment": "SFT",
    "Vehicles": "VHC",
    "Furniture": "FRN",
}


def create_category_pools(upload_folder):
    source_folder = Path(__file__).resolve().parent / "seed_assets"
    preset_root = upload_folder / "presets"
    preset_root.mkdir(parents=True, exist_ok=True)

    for category, source_name in CATEGORY_SOURCES.items():
        category_folder = preset_root / category.lower().replace(" ", "-")
        category_folder.mkdir(parents=True, exist_ok=True)
        for existing in category_folder.glob("*.jpg"):
            existing.unlink()

        with Image.open(source_folder / source_name).convert("RGB") as source:
            source = source.resize((1200, 900), Image.Resampling.LANCZOS)
            for variant in range(1, 6):
                crop = 720 - variant * 8
                left = (1200 - crop) // 2
                top = (900 - crop) // 2
                image = source.crop((left, top, left + crop, top + crop))
                image = image.resize((960, 720), Image.Resampling.LANCZOS)
                image = ImageEnhance.Brightness(image).enhance(
                    0.94 + variant * 0.018
                )
                image = ImageEnhance.Contrast(image).enhance(
                    0.98 + variant * 0.02
                )
                filename = f"{category.lower().replace(' ', '-')}-{variant:02d}.jpg"
                image.save(category_folder / filename, "JPEG", quality=91)


with app.app_context():
    database = app.extensions["database"]
    upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
    upload_folder.mkdir(parents=True, exist_ok=True)

    create_category_pools(upload_folder)

    for old_photo in upload_folder.glob("sample-*.jpg"):
        old_photo.unlink()

    with database.connect() as connection:
        connection.execute("DELETE FROM assets")
        connection.execute("DELETE FROM preset_usage")

    asset_number = 1
    for category, source_name in CATEGORY_SOURCES.items():
        category_folder = category.lower().replace(" ", "-")
        for position in range(1, 6):
            identifier = (
                f"WH-{CATEGORY_PREFIXES[category]}-{asset_number:03d}"
            )
            filename = f"{category_folder}-{position:02d}.jpg"
            photograph_path = f"uploads/presets/{category_folder}/{filename}"

            with database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO preset_usage (category, filename, used_at)
                    VALUES (?, ?, datetime('now'))
                    """,
                    (category, filename),
                )
                connection.execute(
                    """
                    INSERT INTO assets
                    (asset_identifier, category, photograph_path, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (identifier, category, photograph_path),
                )
            asset_number += 1

print("Seed data initialized with 35 strict category-matched preset assets.")
