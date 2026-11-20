import os
import sys
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

        categories = list(CATEGORY_SOURCES)
        asset_number = 1
        for category in categories:
            source_name = CATEGORY_SOURCES[category]
            for position in range(1, 6):
                identifier = f"WH-{CATEGORY_PREFIXES[category]}-{asset_number:03d}"
                filename = f"sample-{identifier.lower().replace('/', '-')}.jpg"

                with Image.open(source_folder / source_name).convert("RGB") as base:
                    base = base.resize((960, 720), Image.Resampling.LANCZOS)
                    base = ImageEnhance.Brightness(base).enhance(
                        0.82 + ((asset_number % 7) * 0.055)
                    )
                    base = ImageEnhance.Contrast(base).enhance(
                        1.05 + ((asset_number % 5) * 0.07)
                    )
                    base = ImageEnhance.Color(base).enhance(
                        0.82 + ((asset_number % 6) * 0.12)
                    )
                    tint = TINTS[category]
                    tint_layer = Image.new("RGB", base.size, tint)
                    base = Image.blend(
                        base,
                        tint_layer,
                        0.035 + ((asset_number % 4) * 0.012),
                    )
                    base.save(upload_folder / filename, "JPEG", quality=88)

                with database.connect() as connection:
                    connection.execute(
                        """
                        INSERT INTO assets
                        (asset_identifier, category, photograph_path, created_at)
                        VALUES (?, ?, ?, datetime('now'))
                        """,
                        (
                            identifier,
                            category,
                            f"uploads/{filename}",
                        ),
                    )
                asset_number += 1


seed_demo_assets()
