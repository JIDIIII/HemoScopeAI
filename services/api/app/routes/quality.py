from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import ValidationError

from app.core.errors import APIError
from app.schemas.errors import ErrorResponse
from app.schemas.quality import CaptureMetadata, QualityResponse
from app.services.image_quality import assess_image_quality
from app.utils.uploads import read_image_upload

router = APIRouter(tags=["quality"])


@router.post(
    "/quality",
    response_model=QualityResponse,
    responses={
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
    },
)
async def check_quality(
    request: Request,
    image: UploadFile = File(..., description="JPEG, PNG, or WebP microscope field image."),
    capture_metadata: str | None = Form(default=None),
) -> QualityResponse:
    settings = request.app.state.settings
    if capture_metadata:
        try:
            CaptureMetadata.model_validate_json(capture_metadata)
        except ValidationError as exc:
            raise APIError(
                422,
                "invalid_capture_metadata",
                "Capture metadata must contain only allowed non-identifying fields.",
            ) from exc
    image_bytes = await read_image_upload(image, settings)
    return assess_image_quality(
        image_bytes,
        image.content_type,
        settings,
        image_kind="field",
    )
