from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, Request, UploadFile

from app.core.errors import APIError
from app.schemas.analysis import AnalysisResponse, AnalysisStatus
from app.schemas.errors import ErrorResponse
from app.schemas.quality import QualityStatus
from app.services.image_preprocessing import prepare_image_for_inference
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
        503: {"model": ErrorResponse},
    },
)
async def analyze_cell(
    request: Request,
    cell_crop: UploadFile = File(..., description="Confirmed single-cell crop."),
    crop_confirmed: bool = Form(...),
    research_session_id: UUID | None = Form(default=None),
) -> AnalysisResponse:
    if not crop_confirmed:
        raise APIError(
            422,
            "crop_confirmation_required",
            "Confirm that the crop contains one complete cell before analysis.",
        )

    settings = request.app.state.settings
    image_bytes = await read_image_upload(cell_crop, settings)
    quality = assess_image_quality(
        image_bytes,
        cell_crop.content_type,
        settings,
        image_kind="crop",
    )
    analysis_id = uuid4()
    if not quality.acceptable:
        return AnalysisResponse(
            analysis_id=analysis_id,
            analysis_status=AnalysisStatus.RECAPTURE_REQUIRED,
            quality_status=QualityStatus.REJECTED,
            research_session_id=research_session_id,
            warning=(
                "This crop failed the development quality gate. No classification "
                "was performed. Review the image and recapture or choose another cell."
            ),
        )

    adapter = request.app.state.inference_adapter
    prepared_image = prepare_image_for_inference(
        image_bytes,
        cell_crop.content_type,
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

    return AnalysisResponse(
        analysis_id=analysis_id,
        analysis_status=result.analysis_status,
        quality_status=QualityStatus.ACCEPTED,
        model_label=result.model_label,
        raw_model_score=result.raw_model_score,
        model_version=result.model_version,
        inference_mode=result.inference_mode,
        research_session_id=research_session_id,
        warning=result.warning or RESEARCH_WARNING,
    )
