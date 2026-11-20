import io
import os
import tempfile

import pytest
from PIL import Image

from app import create_app


@pytest.fixture()
def environment():
    directory = tempfile.TemporaryDirectory()
    upload_folder = os.path.join(directory.name, "uploads")
    categories = [
        "electronics",
        "tools",
        "machinery",
        "other",
        "safety-equipment",
        "vehicles",
        "furniture",
    ]
    for category in categories:
        preset_folder = os.path.join(upload_folder, "presets", category)
        os.makedirs(preset_folder, exist_ok=True)
        for variant in range(1, 6):
            with Image.new("RGB", (40, 30), "gray") as image:
                image.save(
                    os.path.join(preset_folder, f"{category}-{variant:02d}.jpg"),
                    "JPEG",
                )
    app = create_app(
        {
            "TESTING": True,
            "DATABASE": os.path.join(directory.name, "test.db"),
            "UPLOAD_FOLDER": upload_folder,
            "ALLOWED_ORIGINS": ["http://localhost:5173"],
            "MAX_CONTENT_LENGTH": 5 * 1024 * 1024,
        }
    )
    yield app
    directory.cleanup()


@pytest.fixture()
def client(environment):
    return environment.test_client()


def image_bytes(name="asset.png", content=b"not-a-real-image"):
    return (io.BytesIO(content), name)


def create_payload(asset_id="WH-TEST-001", category="Tools", image_name="asset.png"):
    stream = io.BytesIO()
    Image.new("RGB", (20, 20), "gray").save(stream, "PNG")
    stream.seek(0)
    return {
        "asset_identifier": asset_id,
        "category": category,
        "photograph": (stream, image_name, "image/png"),
    }


def test_database_initializes(environment):
    database = environment.extensions["database"]
    with database.connect() as connection:
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='assets'"
        ).fetchone()
    assert table is not None


def test_create_asset(client):
    response = client.post("/api/assets", data=create_payload(), content_type="multipart/form-data")
    assert response.status_code == 201
    body = response.get_json()
    assert body["asset_identifier"] == "WH-TEST-001"
    assert body["category"] == "Tools"
    assert body["created_at"]
    assert body["photograph_url"].endswith("/photograph")


def test_create_asset_without_upload_uses_category_preset(client):
    response = client.post(
        "/api/assets",
        data={"asset_identifier": "WH-MCH-PRESET", "category": "Machinery"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    body = response.get_json()
    assert "/presets/machinery/" in body["photograph_path"]
    photograph = client.get(body["photograph_url"])
    assert photograph.status_code == 200


def test_repeated_category_presets_use_distinct_images(client):
    paths = []
    for index in range(1, 4):
        response = client.post(
            "/api/assets",
            data={"asset_identifier": f"WH-FRN-{index}", "category": "Furniture"},
            content_type="multipart/form-data",
        )
        assert response.status_code == 201
        paths.append(response.get_json()["photograph_path"])
    assert len(set(paths)) == 3


def test_duplicate_asset_id_returns_conflict(client):
    first = client.post("/api/assets", data=create_payload(), content_type="multipart/form-data")
    assert first.status_code == 201
    second = client.post(
        "/api/assets",
        data=create_payload(" wh-test-001 "),
        content_type="multipart/form-data",
    )
    assert second.status_code == 409
    assert "already exists" in second.get_json()["error"]


def test_search_is_case_insensitive(client):
    client.post("/api/assets", data=create_payload("Alpha-123"), content_type="multipart/form-data")
    response = client.get("/api/assets?search=ALPHA&page=1&limit=10")
    assert response.status_code == 200
    body = response.get_json()
    assert body["pagination"]["total"] == 1
    assert body["items"][0]["asset_identifier"] == "Alpha-123"


def test_fetch_individual_asset(client):
    created = client.post("/api/assets", data=create_payload(), content_type="multipart/form-data")
    asset_id = created.get_json()["id"]
    response = client.get(f"/api/assets/{asset_id}")
    assert response.status_code == 200
    assert response.get_json()["asset_identifier"] == "WH-TEST-001"


def test_reject_invalid_image_type(client):
    payload = {
        "asset_identifier": "BAD-TYPE",
        "category": "Tools",
        "photograph": (io.BytesIO(b"plain text"), "asset.txt", "text/plain"),
    }
    response = client.post("/api/assets", data=payload, content_type="multipart/form-data")
    assert response.status_code == 400
    assert "PNG" in response.get_json()["error"]


def test_reject_oversized_image(client):
    payload = {
        "asset_identifier": "BIG-FILE",
        "category": "Tools",
        "photograph": (io.BytesIO(b"x" * (5 * 1024 * 1024 + 1)), "asset.png", "image/png"),
    }
    response = client.post("/api/assets", data=payload, content_type="multipart/form-data")
    assert response.status_code == 413


@pytest.mark.parametrize(
    ("data", "message"),
    [
        ({"category": "Tools"}, "Asset ID"),
        (
            {"asset_identifier": "WH-1", "category": "Unknown"},
            "category",
        ),
    ],
)
def test_api_validation(client, data, message):
    response = client.post("/api/assets", data=data, content_type="multipart/form-data")
    assert response.status_code == 400
    assert message.lower() in response.get_json()["error"].lower()
