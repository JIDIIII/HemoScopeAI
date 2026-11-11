from fastapi import APIRouter, Request

from app.schemas.analysis import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    adapter = request.app.state.inference_adapter
    return HealthResponse(
        service_status="ok",
        api_version=settings.api_version,
        model_available=adapter.model_available,
        model_version=adapter.model_version,
        inference_mode=adapter.inference_mode,
    )
