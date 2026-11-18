# HemoScope AI API contract

The Pydantic models are authoritative. The current OpenAPI snapshot is packages/contracts/openapi.json, and the mobile type file is generated from that JSON.

When `HEMOSCOPE_AUTH_MODE=supabase`, `POST /quality`, `POST /analyze`, and `GET /session/{id}` require `Authorization: Bearer <Supabase access token>`. The API validates the token with Supabase Auth before parsing an upload body. `GET /health` stays public and reports service availability only. Local development keeps authentication disabled by default. Authentication uses an HTTP header and does not change the request or response JSON contract.

## Routes

| Method and path   | Input                                                                                  | Output                                                                                                                  | Current behavior                                                                  |
| ----------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| GET /health       | None                                                                                   | service_status, api_version, model availability/version, inference mode                                                 | Available without a model                                                         |
| POST /quality     | Multipart image; optional capture_metadata JSON                                        | acceptable, measurements, rejection reasons, recapture instructions                                                     | Runs development quality checks                                                   |
| POST /analyze     | Multipart cell_crop, crop_confirmed, optional crop_bounds JSON and research_session_id | analysis_id, request_id, status, quality status, rejection reasons/instructions, optional model output/version, ALL-class score, decision-policy version, warning | Rechecks/extracts crop; without a model returns an explicit inconclusive response |
| GET /session/{id} | UUID path parameter                                                                    | Session metadata                                                                                                        | Returns server_sessions_disabled until persistence and authorization exist        |

POST /feedback is reserved for later qualified-review workflows and is not exposed.

## Upload rules

Allowed formats are JPEG, PNG, and WebP. The service checks the media type, file content, decoded dimensions, configured pixel ceiling, and maximum upload size. A rejected field does not proceed to cell classification. The analysis route checks crop confirmation and crop quality before invoking the adapter.

Optional capture metadata may include only capture_profile_id, objective_magnification, and capture_sequence_index. Patient names, slide labels, and operator identifiers are not accepted. Metadata is not persisted by this API.

For `/analyze`, `cell_crop` may be an already-extracted cell crop. For the mobile manual-selection path it may contain the source field plus a `crop_bounds` JSON string with normalized `x`, `y`, `width`, and `height` fractions. The backend extracts that rectangle, checks the resulting crop, and only then calls the inference adapter. Crop bounds must remain inside the image.

## Analysis status values

- recapture_required: file or crop failed a quality gate; no inference was performed.
- inconclusive: a model abstained, no model is configured, or an explicitly simulated workflow was run. `inference_mode` distinguishes `real`, `simulated`, and `unavailable`.
- review_required: a model output requires qualified review.
- analysis_complete: a model returned a completed scoped output. Under Option B, an ALL-class score below 0.30 uses this status and the warning must say: “No model flag at this research threshold. This does not rule out disease.”
- error: reserved status for typed client workflows; current API errors use a structured error envelope and appropriate HTTP status.

For real inference, `/analyze` returns `all_score` (the model's output for the explicit `all` class) and `decision_policy_version`. The app may show the ALL-class score only in technical details and must identify it as uncalibrated; it must not show the raw argmax label or winning-class `raw_model_score` to users. The app renders the API's status and `warning` message instead of deriving policy from either raw argmax field. The warning also carries the research-use disclaimer. Option B maps `[0.30, 0.70)` to `inconclusive` and `>=0.70` to `review_required`.

None of these values means a patient has or does not have leukemia. A request failure must not be rendered as a negative result.

## Error envelope

Every analysis response includes a request ID matching the `X-Request-ID` header. Genuine inference results must include a model version, `all_score`, and `decision_policy_version`. No-model local mode returns HTTP 200 with `analysis_status=inconclusive`, `inference_mode=unavailable`, and no label or scores so the app can complete the flow without fabricating a prediction. Simulated mode likewise returns no classification or score and is clearly marked simulated. A configured but unavailable provider returns an error.

Errors use an ErrorResponse containing code, message, request_id, and optional details. Expected codes include authentication_required, authentication_provider_unavailable, unsupported_media_type, file_format_mismatch, image_decode_failed, image_dimensions_too_large, invalid_image_dimensions, empty_upload, upload_too_large, invalid_crop_bounds, crop_confirmation_required, request_validation_error, model_unavailable, inference_response_invalid, and server_sessions_disabled.

The API version may change while this is a scaffold. Update Pydantic schemas, OpenAPI JSON, generated mobile types, tests, and this document in one contract change.
