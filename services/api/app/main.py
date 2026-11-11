from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import Settings
from app.core.errors import APIError
from app.core.security import create_request_id
from app.routes import analyze, health, quality, sessions
from app.schemas.errors import ErrorDetail, ErrorResponse
from app.services.inference import InferenceAdapter, build_inference_adapter


def create_app(
    settings: Settings | None = None,
    inference_adapter: InferenceAdapter | None = None,
) -> FastAPI:
    application = FastAPI(
        title="HemoScope AI Research API",
        version=(settings or Settings()).api_version,
        description=(
            "Research-use image quality and selected-cell morphology screening API. "
            "It is not a medical diagnostic service."
        ),
    )
    application.state.settings = settings or Settings()
    application.state.inference_adapter = inference_adapter or build_inference_adapter(
        application.state.settings
    )

    @application.middleware("http")
    async def attach_request_id(request: Request, call_next: Callable) -> JSONResponse:
        request.state.request_id = create_request_id()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        return response

    @application.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        payload = ErrorResponse(
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                request_id=getattr(request.state, "request_id", "unavailable"),
                details=exc.details,
            )
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = [
            {
                "location": [str(item) for item in error.get("loc", ())],
                "message": error.get("msg", "Invalid request."),
            }
            for error in exc.errors()
        ]
        payload = ErrorResponse(
            error=ErrorDetail(
                code="request_validation_error",
                message="The request did not match the API contract.",
                request_id=getattr(request.state, "request_id", "unavailable"),
                details={"fields": errors},
            )
        )
        return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))

    @application.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        message = (
            exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
        )
        payload = ErrorResponse(
            error=ErrorDetail(
                code="http_error",
                message=message,
                request_id=getattr(request.state, "request_id", "unavailable"),
            )
        )
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))

    @application.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        del exc
        payload = ErrorResponse(
            error=ErrorDetail(
                code="internal_error",
                message="The request could not be completed.",
                request_id=getattr(request.state, "request_id", "unavailable"),
            )
        )
        return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))

    application.include_router(health.router)
    application.include_router(quality.router)
    application.include_router(analyze.router)
    application.include_router(sessions.router)
    return application


app = create_app()
