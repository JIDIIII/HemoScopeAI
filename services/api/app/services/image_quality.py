from __future__ import annotations

import warnings
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import APIError
from app.schemas.quality import (
    QualityMeasurements,
    QualityRejectionReason,
    QualityResponse,
    QualityStatus,
)

if TYPE_CHECKING:
    from app.core.config import Settings

try:
    import cv2
except ImportError:  # Allows basic image-quality tests in minimal offline environments.
    cv2 = None


@dataclass(frozen=True)
class DecodedImage:
    rgb: np.ndarray
    width: int
    height: int
    file_format: str


MIME_TO_FORMAT = {
    "image/jpeg": "JPEG",
    "image/jpg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def decode_image(
    image_bytes: bytes,
    content_type: str | None,
    max_image_pixels: int = 40_000_000,
) -> DecodedImage:
    normalized_type = (content_type or "").split(";", maxsplit=1)[0].strip().lower()
    expected_format = MIME_TO_FORMAT.get(normalized_type)
    if expected_format is None:
        raise APIError(
            415,
            "unsupported_media_type",
            "Upload a JPEG, PNG, or WebP image.",
        )

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(image_bytes)) as source:
                actual_format = (source.format or "").upper()
                if actual_format != expected_format:
                    raise APIError(
                        415,
                        "file_format_mismatch",
                        "The uploaded file content does not match its declared image format.",
                    )
                oriented = ImageOps.exif_transpose(source)
                width, height = oriented.size
                if width * height > max_image_pixels:
                    raise APIError(
                        413,
                        "image_dimensions_too_large",
                        "The decoded image exceeds the configured pixel limit.",
                    )
                oriented.load()
                rgb = np.asarray(oriented.convert("RGB"), dtype=np.uint8)
    except APIError:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise APIError(
            413,
            "image_dimensions_too_large",
            "The decoded image exceeds the configured pixel limit.",
        ) from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise APIError(
            422,
            "image_decode_failed",
            "The uploaded image could not be decoded. Choose a valid JPEG, PNG, or WebP file.",
        ) from exc

    if width < 1 or height < 1:
        raise APIError(422, "invalid_image_dimensions", "The image has invalid dimensions.")
    return DecodedImage(rgb=rgb, width=width, height=height, file_format=actual_format)


def _gray_image(rgb: np.ndarray) -> np.ndarray:
    if cv2 is not None:
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    channels = rgb.astype(np.float32)
    return np.clip(
        0.299 * channels[:, :, 0] + 0.587 * channels[:, :, 1] + 0.114 * channels[:, :, 2],
        0,
        255,
    ).astype(np.uint8)


def _laplacian_variance(gray: np.ndarray) -> float:
    if cv2 is not None:
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    values = gray.astype(np.float32)
    padded = np.pad(values, 1, mode="edge")
    laplacian = (
        padded[:-2, 1:-1] + padded[2:, 1:-1] + padded[1:-1, :-2] + padded[1:-1, 2:] - 4 * values
    )
    return float(laplacian.var())


def assess_image_quality(
    image_bytes: bytes,
    content_type: str | None,
    settings: Settings,
    *,
    image_kind: str = "field",
) -> QualityResponse:
    decoded = decode_image(image_bytes, content_type, settings.max_image_pixels)
    gray = _gray_image(decoded.rgb)
    brightness = float(gray.mean())
    blur_score = _laplacian_variance(gray)
    overexposed = float(np.mean(gray >= 250))
    underexposed = float(np.mean(gray <= 5))

    if image_kind == "crop":
        min_width = settings.quality_min_crop_width
        min_height = settings.quality_min_crop_height
    else:
        min_width = settings.quality_min_field_width
        min_height = settings.quality_min_field_height

    measurements = QualityMeasurements(
        width=decoded.width,
        height=decoded.height,
        file_format=decoded.file_format,
        blur_score=blur_score,
        mean_brightness=brightness,
        overexposed_fraction=overexposed,
        underexposed_fraction=underexposed,
    )
    reasons: list[QualityRejectionReason] = []

    if decoded.width < min_width or decoded.height < min_height:
        reasons.append(
            QualityRejectionReason(
                code="minimum_dimensions",
                message=(
                    f"Image is smaller than the development minimum of {min_width} × {min_height}."
                ),
                instructions=(
                    "Use a higher-resolution capture and keep the full field or cell in frame."
                ),
            )
        )
    if blur_score < settings.quality_min_laplacian_variance:
        reasons.append(
            QualityRejectionReason(
                code="focus_or_blur",
                message=(
                    "The image has low high-frequency detail under the development focus check."
                ),
                instructions=(
                    "Stabilize the phone, refocus through the microscope, and capture again."
                ),
            )
        )
    if brightness < settings.quality_min_mean_brightness:
        reasons.append(
            QualityRejectionReason(
                code="underexposure",
                message="The image is darker than the development exposure range.",
                instructions="Increase microscope illumination or exposure, then recapture.",
            )
        )
    if brightness > settings.quality_max_mean_brightness:
        reasons.append(
            QualityRejectionReason(
                code="overexposure",
                message="The image is brighter than the development exposure range.",
                instructions="Reduce illumination or exposure, then recapture.",
            )
        )
    if overexposed > settings.quality_max_overexposed_fraction:
        reasons.append(
            QualityRejectionReason(
                code="clipped_highlights",
                message="Too many image pixels are clipped near white.",
                instructions="Reduce illumination or exposure and avoid glare before recapturing.",
            )
        )
    if underexposed > settings.quality_max_underexposed_fraction:
        reasons.append(
            QualityRejectionReason(
                code="clipped_shadows",
                message="Too many image pixels are clipped near black.",
                instructions="Increase illumination and check for vignetting before recapturing.",
            )
        )

    instructions = list(dict.fromkeys(reason.instructions for reason in reasons))
    return QualityResponse(
        acceptable=not reasons,
        quality_status=QualityStatus.ACCEPTED if not reasons else QualityStatus.REJECTED,
        measurements=measurements,
        rejection_reasons=reasons,
        actionable_instructions=instructions,
    )
