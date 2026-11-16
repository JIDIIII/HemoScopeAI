#!/usr/bin/env python3
"""Export the Pydantic API schemas as the committed OpenAPI contract snapshot."""

from __future__ import annotations

import json
import sys
from enum import Enum
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "api"))

from app.schemas.analysis import (  # noqa: E402
    AnalysisResponse,
    AnalysisStatus,
    HealthResponse,
    InferenceMode,
    SessionMetadata,
)
from app.schemas.errors import ErrorDetail, ErrorResponse  # noqa: E402
from app.schemas.quality import (  # noqa: E402
    CaptureMetadata,
    QualityMeasurements,
    QualityRejectionReason,
    QualityResponse,
    QualityStatus,
)


def schema_for(model: type) -> dict[str, Any]:
    if issubclass(model, Enum):
        return {
            model.__name__: {
                "title": model.__name__,
                "type": "string",
                "enum": [item.value for item in model],
            }
        }
    schema = model.model_json_schema(ref_template="#/components/schemas/{model}")
    definitions = schema.pop("$defs", {})
    return {**definitions, model.__name__: schema}


def response_schema(name: str, description: str) -> dict[str, Any]:
    return {
        "description": description,
        "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{name}"}}},
    }


def error_responses(*status_codes: int) -> dict[str, Any]:
    return {
        str(status_code): response_schema("ErrorResponse", "Structured API error.")
        for status_code in status_codes
    }


def multipart_body(properties: dict[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "required": True,
        "content": {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        },
    }


def build_openapi() -> dict[str, Any]:
    models = [
        AnalysisResponse,
        AnalysisStatus,
        CaptureMetadata,
        ErrorDetail,
        ErrorResponse,
        HealthResponse,
        InferenceMode,
        QualityMeasurements,
        QualityRejectionReason,
        QualityResponse,
        QualityStatus,
        SessionMetadata,
    ]
    schemas: dict[str, Any] = {}
    for model in models:
        schemas.update(schema_for(model))

    return {
        "openapi": "3.1.0",
        "info": {
            "title": "HemoScope AI Research API",
            "version": "0.1.0",
            "description": (
                "Research-use image quality and selected-cell morphology screening API. "
                "It is not a medical diagnostic service."
            ),
        },
        "paths": {
            "/health": {
                "get": {
                    "operationId": "getHealth",
                    "tags": ["health"],
                    "responses": {
                        "200": response_schema("HealthResponse", "Service and model availability.")
                    },
                }
            },
            "/quality": {
                "post": {
                    "operationId": "checkQuality",
                    "tags": ["quality"],
                    "requestBody": multipart_body(
                        {
                            "image": {"type": "string", "format": "binary"},
                            "capture_metadata": {
                                "type": "string",
                                "description": "Optional JSON with non-identifying setup fields.",
                            },
                        },
                        ["image"],
                    ),
                    "responses": {
                        "200": response_schema(
                            "QualityResponse", "Quality measurements and recapture guidance."
                        ),
                        **error_responses(413, 415, 422),
                    },
                }
            },
            "/analyze": {
                "post": {
                    "operationId": "analyzeCell",
                    "tags": ["analysis"],
                    "requestBody": multipart_body(
                        {
                            "cell_crop": {"type": "string", "format": "binary"},
                            "crop_confirmed": {"type": "boolean"},
                            "research_session_id": {
                                "type": "string",
                                "format": "uuid",
                                "nullable": True,
                            },
                        },
                        ["cell_crop", "crop_confirmed"],
                    ),
                    "responses": {
                        "200": response_schema(
                            "AnalysisResponse",
                            "Selected-cell result, recapture state, or explicit simulation.",
                        ),
                        **error_responses(413, 415, 422, 503),
                    },
                }
            },
            "/session/{session_id}": {
                "get": {
                    "operationId": "getSession",
                    "tags": ["sessions"],
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"},
                        }
                    ],
                    "responses": {
                        "200": response_schema(
                            "SessionMetadata", "Authorized research session metadata."
                        ),
                        **error_responses(404, 501),
                    },
                }
            },
        },
        "components": {"schemas": schemas},
    }


def main() -> None:
    destination = ROOT / "packages" / "contracts" / "openapi.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_openapi(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
