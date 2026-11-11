# API contracts

The FastAPI Pydantic schemas are the source of truth. Run python3 scripts/export_openapi.py to regenerate openapi.json, then python3 scripts/generate_api_types.py to regenerate the mobile TypeScript schema types.

CI regenerates both files and checks for a diff. Change the Pydantic models first, commit the OpenAPI snapshot and generated TypeScript type file together, and coordinate contract changes with all module owners. Multipart image fields are documented in OpenAPI; they are represented as binary strings in the request schema.

The analysis status values are recapture_required, inconclusive, review_required, analysis_complete, and error. Do not use a failed analysis as a negative result.
