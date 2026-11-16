from fastapi import UploadFile

from app.core.config import Settings
from app.core.errors import APIError

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}


async def read_image_upload(upload: UploadFile, settings: Settings) -> bytes:
    content_type = (upload.content_type or "").split(";", maxsplit=1)[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise APIError(
            415,
            "unsupported_media_type",
            "Upload a JPEG, PNG, or WebP image.",
        )

    image_bytes = await upload.read(settings.max_upload_bytes + 1)
    if len(image_bytes) > settings.max_upload_bytes:
        raise APIError(
            413,
            "upload_too_large",
            f"Image uploads are limited to {settings.max_upload_bytes} bytes.",
        )
    if not image_bytes:
        raise APIError(422, "empty_upload", "The uploaded image is empty.")
    return image_bytes
