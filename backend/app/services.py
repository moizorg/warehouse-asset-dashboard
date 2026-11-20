import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from werkzeug.utils import secure_filename

CATEGORIES = {
    "Machinery",
    "Tools",
    "Electronics",
    "Furniture",
    "Vehicles",
    "Safety Equipment",
    "Other",
}
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,63}$")


class ValidationError(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def validate_asset_identifier(value):
    identifier = (value or "").strip()
    if not identifier:
        raise ValidationError("Asset ID is required.")
    if not IDENTIFIER_PATTERN.fullmatch(identifier):
        raise ValidationError(
            "Asset ID may contain 1-64 letters, numbers, periods, underscores, slashes, or hyphens."
        )
    return identifier


def validate_category(value):
    category = (value or "").strip()
    if not category:
        raise ValidationError("Asset category is required.")
    if category not in CATEGORIES:
        raise ValidationError("Asset category is invalid.")
    return category


def validate_image(file):
    if not file or not file.filename:
        raise ValidationError("An asset photograph is required.")
    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("Only PNG, JPG, and JPEG image files are accepted.")
    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size <= 0:
        raise ValidationError("The uploaded photograph is empty.")
    if size > MAX_IMAGE_BYTES:
        raise ValidationError("File must be 5 MB or smaller.")
    try:
        file.stream.seek(0)
        with Image.open(file.stream) as image:
            image.verify()
    except (UnidentifiedImageError, OSError):
        raise ValidationError("The uploaded file is not a valid PNG, JPG, or JPEG image.")
    finally:
        file.stream.seek(0)
    return filename, extension


def save_image(file, upload_folder):
    _, extension = validate_image(file)
    generated_name = f"{uuid.uuid4().hex}.{extension}"
    destination = Path(upload_folder).resolve() / generated_name
    file.save(destination)
    return f"uploads/{generated_name}"
