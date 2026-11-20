from pathlib import Path
import random
from PIL import Image, ImageEnhance
from app import create_app


app = create_app()

photo_dir = Path(__file__).resolve().parent / "seed_assets"

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

category_prefixes = {
    "Machinery": "MCH",
    "Tools": "TLS",
    "Electronics": "ELC",
    "Furniture": "FRN",
    "Vehicles": "VHC",
    "Safety Equipment": "SFT",
}

category_hue_shifts = {
    "Machinery": (10, 55, 115, 175, 235),
    "Tools": (0, 35, 85, 145, 205),
    "Electronics": (0, 50, 105, 165, 220),
    "Furniture": (0, 40, 95, 155, 210),
    "Vehicles": (0, 30, 80, 140, 200),
    "Safety Equipment": (0, 25, 70, 125, 185),
}

category_color_tints = {
    "Machinery": (232, 114, 62),
    "Tools": (226, 166, 74),
    "Electronics": (72, 142, 176),
    "Furniture": (205, 126, 82),
    "Vehicles": (112, 130, 150),
    "Safety Equipment": (224, 178, 52),
}


def apply_asset_color_variant(image, category, occurrence):
    hue_shift = round(category_hue_shifts[category][occurrence] * 255 / 360)
    hsv = image.convert("HSV")
    hue, saturation, value = hsv.split()
    hue = hue.point(lambda channel: (channel + hue_shift) % 256)
    saturation = saturation.point(
        lambda channel: max(0, min(255, int(channel * (1.12 + occurrence * 0.08))))
    )
    value = value.point(
        lambda channel: max(0, min(255, int(channel * (0.94 + occurrence * 0.025))))
    )
    variant = Image.merge("HSV", (hue, saturation, value)).convert("RGB")
    tint = Image.new("RGB", variant.size, category_color_tints[category])
    return Image.blend(
        variant,
        tint,
        0.055 + occurrence * 0.018,
    )

with app.app_context():
    database = app.extensions["database"]
    upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
    upload_folder.mkdir(parents=True, exist_ok=True)

    for old_photo in upload_folder.glob("sample-*.jpg"):
        old_photo.unlink()

    with database.connect() as connection:
        connection.execute("DELETE FROM assets")

    randomized_categories = [
        category
        for category in category_names
        for _ in range(5)
    ]
    random.Random(2026).shuffle(randomized_categories)

    category_counts = {category: 0 for category in category_names}
    for category in randomized_categories:
        category_counts[category] += 1
        occurrence = category_counts[category] - 1
        identifier = (
            f"WH-{category_prefixes[category]}-{category_counts[category]:03d}"
        )
        filename = f"sample-{identifier.lower().replace('/', '-')}.jpg"
        source_photo = photo_dir / category_photos[category]
        with Image.open(source_photo).convert("RGB") as base:
            base = base.resize((960, 720))
            unique_image = apply_asset_color_variant(base, category, occurrence)
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
