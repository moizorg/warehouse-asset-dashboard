import os
import sys
import random
from pathlib import Path
from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

deployment_url = os.getenv("VERCEL_PROJECT_PRODUCTION_URL") or os.getenv("VERCEL_URL")
approved_origins = os.getenv("ALLOWED_ORIGINS", "")
if deployment_url:
    approved_origins = ",".join(
        origin for origin in (
            approved_origins,
            f"https://{deployment_url}",
        ) if origin
    )
os.environ["ALLOWED_ORIGINS"] = approved_origins or "http://localhost:5173"
if not os.getenv("TURSO_DATABASE_URL"):
    os.environ["DATABASE_PATH"] = os.getenv("DATABASE_PATH", "/tmp/warehouse-assets.db")
os.environ["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "/tmp/warehouse-uploads")

from app import create_app


app = create_app()

CATEGORY_SOURCES = {
    "Machinery": "machinery.jpg",
    "Tools": "tools.jpg",
    "Electronics": "electronics.jpg",
    "Furniture": "furniture.jpg",
    "Vehicles": "vehicles.jpg",
    "Safety Equipment": "safety.jpg",
}
CATEGORY_PREFIXES = {
    "Machinery": "MCH",
    "Tools": "TLS",
    "Electronics": "ELC",
    "Furniture": "FRN",
    "Vehicles": "VHC",
    "Safety Equipment": "SFT",
}
TINTS = {
    "Machinery": (232, 114, 62),
    "Tools": (226, 166, 74),
    "Electronics": (72, 142, 176),
    "Furniture": (205, 126, 82),
    "Vehicles": (112, 130, 150),
    "Safety Equipment": (224, 178, 52),
}

HUE_SHIFTS = {
    "Machinery": (10, 55, 115, 175, 235),
    "Tools": (0, 35, 85, 145, 205),
    "Electronics": (0, 50, 105, 165, 220),
    "Furniture": (0, 40, 95, 155, 210),
    "Vehicles": (0, 30, 80, 140, 200),
    "Safety Equipment": (0, 25, 70, 125, 185),
}


def apply_asset_color_variant(image, category, occurrence):
    hue_shift = round(HUE_SHIFTS[category][occurrence] * 255 / 360)
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
    tint = Image.new("RGB", variant.size, TINTS[category])
    return Image.blend(
        variant,
        tint,
        0.055 + occurrence * 0.018,
    )

def seed_demo_assets():
    with app.app_context():
        database = app.extensions["database"]
        upload_folder = Path(app.config["UPLOAD_FOLDER"]).resolve()
        upload_folder.mkdir(parents=True, exist_ok=True)
        source_folder = BACKEND / "seed_assets"

        with database.connect() as connection:
            total = connection.execute("SELECT COUNT(*) FROM assets").fetchone()[0]
        if total:
            return

        categories = [
            category
            for category in CATEGORY_SOURCES
            for _ in range(5)
        ]
        random.Random(2026).shuffle(categories)

        category_counts = {category: 0 for category in CATEGORY_SOURCES}
        for category in categories:
            category_counts[category] += 1
            occurrence = category_counts[category] - 1
            identifier = (
                f"WH-{CATEGORY_PREFIXES[category]}-{category_counts[category]:03d}"
            )
            filename = f"sample-{identifier.lower().replace('/', '-')}.jpg"
            source_name = CATEGORY_SOURCES[category]

            with Image.open(source_folder / source_name).convert("RGB") as base:
                base = base.resize((960, 720), Image.Resampling.LANCZOS)
                base = apply_asset_color_variant(base, category, occurrence)
                base.save(upload_folder / filename, "JPEG", quality=88)
                with open(upload_folder / filename, "rb") as photograph:
                    photograph_data = photograph.read()

            with database.connect() as connection:
                connection.execute(
                    """
                    INSERT INTO assets
                    (asset_identifier, category, photograph_path, photograph_data, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                    """,
                    (
                        identifier,
                        category,
                        f"uploads/{filename}",
                        photograph_data,
                    ),
                )


seed_demo_assets()
