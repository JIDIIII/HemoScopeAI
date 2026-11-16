from __future__ import annotations

import math
from io import BytesIO
from typing import TYPE_CHECKING

from PIL import Image

from app.schemas.analysis import CropBounds
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


def extract_normalized_crop(
    image_bytes: bytes,
    content_type: str | None,
    settings: Settings,
    bounds: CropBounds,
) -> bytes:
    """Extract a normalized crop from a full-field upload and encode it as PNG."""
    decoded = decode_image(
        image_bytes,
        content_type,
        max_image_pixels=settings.max_image_pixels,
    )
    left = math.floor(bounds.x * decoded.width)
    top = math.floor(bounds.y * decoded.height)
    right = math.ceil((bounds.x + bounds.width) * decoded.width)
    bottom = math.ceil((bounds.y + bounds.height) * decoded.height)
    right = min(decoded.width, max(left + 1, right))
    bottom = min(decoded.height, max(top + 1, bottom))

    crop = Image.fromarray(decoded.rgb).crop((left, top, right, bottom))
    output = BytesIO()
    crop.save(output, format="PNG", optimize=False)
    return output.getvalue()
