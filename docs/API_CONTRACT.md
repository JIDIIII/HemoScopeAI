# HemoScope AI API contract

The Pydantic models are authoritative. The current OpenAPI snapshot is packages/contracts/openapi.json, and the mobile type file is generated from that JSON.

## Routes

| Method and path | Input | Output | Current behavior |
| --- | --- | --- | --- |
| GET /health | None | service_status, api_version, model availability/version, inference mode | Available without a model |
| POST /quality | Multipart image; optional capture_metadata JSON | acceptable, measurements, rejection reasons, recapture instructions | Runs development quality checks |
| POST /analyze | Multipart cell_crop, crop_confirmed, optional research_session_id | analysis_id, status, quality status, optional model output/version, warning | Rechecks crop; model unavailable by default |
| GET /session/{id} | UUID path parameter | Session metadata | Returns server_sessions_disabled until persistence and authorization exist |

POST /feedback is reserved for later qualified-review workflows and is not exposed.

## Upload rules

Allowed formats are JPEG, PNG, and WebP. The service checks the media type, file content, decoded dimensions, configured pixel ceiling, and maximum upload size. A rejected field does not proceed to cell classification. The analysis route checks crop confirmation and crop quality before invoking the adapter.

Optional capture metadata may include only capture_profile_id, objective_magnification, and capture_sequence_index. Patient names, slide labels, and operator identifiers are not accepted. Metadata is not persisted by this API.

## Analysis status values

- recapture_required: file or crop failed a quality gate; no inference was performed.
- inconclusive: a model abstained or a simulated workflow was run.
- review_required: a model output requires qualified review.
- analysis_complete: a model returned a completed scoped output.
- error: reserved status for typed client workflows; current API errors use a structured error envelope and appropriate HTTP status.

None of these values means a patient has or does not have leukemia. A request failure must not be rendered as a negative result.

## Error envelope

Errors use an ErrorResponse containing code, message, request_id, and optional details. Expected codes include unsupported_media_type, image_decode_failed, upload_too_large, crop_confirmation_required, request_validation_error, model_unavailable, and server_sessions_disabled.

The API version may change while this is a scaffold. Update Pydantic schemas, OpenAPI JSON, generated mobile types, tests, and this document in one contract change.
