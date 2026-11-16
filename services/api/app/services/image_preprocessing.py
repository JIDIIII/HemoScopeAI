from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image

from app.services.image_quality import decode_image

if TYPE_CHECKING:
    from app.core.config import Settings

PREPROCESSING_VERSION = "hemo-rgb-png-v0"


def prepare_image_for_inference(
    image_bytes: bytes,
    content_type: str | None,
    settings: Settings,
) -> bytes:
    """Canonicalize an accepted crop to RGB PNG and strip source metadata."""
    decoded = decode_image(
        image_bytes,
        content_type,
        max_image_pixels=settings.max_image_pixels,
    )
    canonical = Image.fromarray(decoded.rgb)
    output = BytesIO()
    canonical.save(output, format="PNG", optimize=False)
    return output.getvalue()
