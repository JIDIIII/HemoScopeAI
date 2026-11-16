from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, Request, UploadFile
from pydantic import ValidationError

from app.core.errors import APIError
from app.schemas.analysis import AnalysisResponse, AnalysisStatus, CropBounds, InferenceMode
from app.schemas.errors import ErrorResponse
from app.schemas.quality import QualityStatus
from app.services.image_preprocessing import extract_normalized_crop, prepare_image_for_inference
from app.services.image_quality import assess_image_quality
from app.services.inference import ModelUnavailableError
from app.utils.uploads import read_image_upload

router = APIRouter(tags=["analysis"])

RESEARCH_WARNING = (
    "Research and educational use only. This selected-cell morphology result "
    "does not diagnose leukemia, rule out disease, or recommend treatment."
)


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    responses={
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
)
async def analyze_cell(
    request: Request,
    cell_crop: UploadFile = File(
        ...,
        description="Confirmed single-cell crop, or source field paired with crop_bounds.",
    ),
    crop_confirmed: bool = Form(...),
    research_session_id: UUID | None = Form(default=None),
    crop_bounds: str | None = Form(
        default=None,
        description=(
            "Optional JSON with normalized x, y, width, and height when cell_crop "
            "contains a full field instead of an already-extracted cell crop."
        ),
    ),
) -> AnalysisResponse:
    if not crop_confirmed:
        raise APIError(
            422,
            "crop_confirmation_required",
            "Confirm that the crop contains one complete cell before analysis.",
        )

    settings = request.app.state.settings
    image_bytes = await read_image_upload(cell_crop, settings)
    image_content_type = cell_crop.content_type
    if crop_bounds is not None:
        try:
            bounds = CropBounds.model_validate_json(crop_bounds)
        except ValidationError as exc:
            raise APIError(
                422,
                "invalid_crop_bounds",
                "Crop bounds must be valid JSON with a rectangle inside the source image.",
            ) from exc
        image_bytes = extract_normalized_crop(
            image_bytes,
            image_content_type,
            settings,
            bounds,
        )
        image_content_type = "image/png"

    quality = assess_image_quality(
        image_bytes,
        image_content_type,
        settings,
        image_kind="crop",
    )
    analysis_id = uuid4()
    if not quality.acceptable:
        return AnalysisResponse(
            analysis_id=analysis_id,
            request_id=request.state.request_id,
            analysis_status=AnalysisStatus.RECAPTURE_REQUIRED,
            quality_status=QualityStatus.REJECTED,
            rejection_reasons=quality.rejection_reasons,
            actionable_instructions=quality.actionable_instructions,
            research_session_id=research_session_id,
            warning=(
                "This crop failed the development quality gate. No classification was "
                "performed. Follow the rejection instructions and recapture or choose another cell."
            ),
        )

    adapter = request.app.state.inference_adapter
    prepared_image = prepare_image_for_inference(
        image_bytes,
        image_content_type,
        settings,
    )
    try:
        result = await adapter.predict(prepared_image, research_session_id)
    except ModelUnavailableError as exc:
        raise APIError(
            503,
            "model_unavailable",
            "No real inference model is available. The image was not classified.",
        ) from exc

    if result.inference_mode == InferenceMode.REAL and not result.model_version:
        raise APIError(
            502,
            "inference_response_invalid",
            "The inference service did not provide a model version.",
        )

    return AnalysisResponse(
        analysis_id=analysis_id,
        request_id=request.state.request_id,
        analysis_status=result.analysis_status,
        quality_status=QualityStatus.ACCEPTED,
        model_label=result.model_label,
        raw_model_score=result.raw_model_score,
        model_version=result.model_version,
        inference_mode=result.inference_mode,
        research_session_id=research_session_id,
        warning=result.warning or RESEARCH_WARNING,
    )
