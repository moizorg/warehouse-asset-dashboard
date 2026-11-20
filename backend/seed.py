from pathlib import Path
from PIL import Image, ImageEnhance

from app import create_app


app = create_app()

category_sources = {
    "Electronics": "electronics.jpg",
    "Tools": "tools.jpg",
    "Machinery": "machinery.jpg",
    "Other": "warehouse.jpg",
    "Safety Equipment": "safety.jpg",
    "Vehicles": "vehicles.jpg",
    "Furniture": "furniture.jpg",
}

category_prefixes = {
    "Electronics": "ELC",
    "Tools": "TLS",
    "Machinery": "MCH",
    "Other": "OTH",
    "Safety Equipment": "SFT",
    "Vehicles": "VHC",
    "Furniture": "FRN",
}


def create_preset_pools(upload_folder):
    source_folder = Path(__file__).resolve().parent / "seed_assets"
    presets_root = Path(upload_folder).resolve() / "presets"
    presets_root.mkdir(parents=True, exist_ok=True)

    for category, source_name in category_sources.items():
        category_folder = presets_root / category.lower().replace(" ", "-")
        category_folder.mkdir(parents=True, exist_ok=True)
        for old_file in category_folder.glob("*.jpg"):
            old_file.unlink()

        with Image.open(source_folder / source_name).convert("RGB") as source:
            source = source.resize((1200, 900), Image.Resampling.LANCZOS)
            for variant in range(1, 6):
                left = (variant - 1) * 32
                top = (variant - 1) * 18
                right = 1200 - ((5 - variant) * 32)
                bottom = 900 - ((5 - variant) * 18)
                image = source.crop((left, top, right, bottom)).resize(
                    (960, 720),
                    Image.Resampling.LANCZOS,
                )
                image = ImageEnhance.Contrast(image).enhance(
                    0.96 + variant * 0.025
                )
                image.save(
                    category_folder / f"{category.lower().replace(' ', '-')}-{variant:02d}.jpg",
                    "JPEG",
                    quality=90,
                )


with app.app_context():
    database = app.extensions["database"]
    upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
    upload_folder.mkdir(parents=True, exist_ok=True)

    create_preset_pools(upload_folder)

    for old_photo in upload_folder.glob("sample-*.jpg"):
        old_photo.unlink()

    with database.connect() as connection:
        connection.execute("DELETE FROM assets")
        connection.execute("DELETE FROM preset_usage")

    categories = list(category_sources)
    number = 1
    for category in categories:
        prefix = category_prefixes[category]
        for position in range(1, 6):
            identifier = f"WH-{prefix}-{number:03d}"
            category_folder = category.lower().replace(" ", "-")
            preset_name = f"{category_folder}-{position:02d}.jpg"
            photograph_path = f"uploads/presets/{category_folder}/{preset_name}"

            with database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO preset_usage (category, filename, used_at)
                    VALUES (?, ?, datetime('now'))
                    """,
                    (category, preset_name),
                )
                connection.execute(
                    """
                    INSERT INTO assets (asset_identifier, category, photograph_path, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (identifier, category, photograph_path),
                )
            number += 1

print("Seed data initialized with 35 category-matched preset assets.")
