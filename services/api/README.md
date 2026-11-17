# HemoScope AI API

FastAPI validates image uploads, evaluates development image-quality heuristics, strips source metadata while canonicalizing accepted cell crops to RGB PNG, and delegates those crops to an inference adapter. OpenAPI is exported to packages/contracts/openapi.json. The service starts without a model.

## Local setup

From the repository root:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e "services/api[dev]"
cp services/api/.env.example services/api/.env
uvicorn app.main:app --reload --host 0.0.0.0 --app-dir services/api
```

OpenAPI and interactive API documentation are available at /openapi.json and /docs on the local server. To call from a physical Android phone, keep the API bound to 0.0.0.0, allow local-network traffic in the computer firewall, and set the app API URL to the computer's LAN IPv4 address.

## API behavior

- GET /health reports service version and whether real model inference is available.
- POST /quality accepts a JPEG, PNG, or WebP field image and optional non-identifying capture metadata.
- POST /analyze requires a confirmed crop. Clients may send an existing crop or a full field plus normalized `crop_bounds` JSON; the backend extracts and checks that ROI before inference. A quality rejection returns `recapture_required` without calling inference. With the default `inference_provider=none`, an accepted crop returns an explicit `inconclusive`/`unavailable` response with no label or score so local app flow works without Huawei or model files. A configured but incomplete cloud adapter returns HTTP 503 with `model_unavailable`.
- Optional local inference runs the versioned handoff checkpoint on CPU after the same crop-quality gate. From the repository root, install `python -m pip install -e "services/api[local-inference]"`, then set `HEMOSCOPE_INFERENCE_PROVIDER=local` in `services/api/.env`. The default checkpoint is under the ignored `ml/artifacts/handoff/hemoscope-inference-handoff-v1` directory; override its bundle location with `HEMOSCOPE_LOCAL_INFERENCE_BUNDLE_DIR` if needed. The model applies its bound Option B policy and returns `all_score`, `decision_policy_version`, status, model version and warning. Missing or incompatible bundle files fail closed as `model_unavailable`; invalid inference results return `inference_response_invalid`.
- GET /session/{id} reports server_sessions_disabled until authenticated server persistence is deliberately added.
- POST /feedback is not exposed.

Every successful analysis response contains a `request_id` matching the `X-Request-ID` header. Real model responses must provide `model_version`, `all_score` and `decision_policy_version`; the mobile app shows the score only in technical details and does not display the raw winning-class label or score. `HEMOSCOPE_ENABLE_DEMO_MOCK` defaults to false. When explicitly set to true, the analysis endpoint returns an inconclusive response with `inference_mode=simulated`, a demo model version, no prediction score, and a visible warning. It only exercises request/response flow and does not fabricate a morphology prediction.

## Quality thresholds

Blur, brightness, clipped-pixel fractions, and minimum dimensions are configurable. Current values are development defaults only; they are not validated microscopy thresholds. Calibrate them on representative microscope images from the target phone and optics before using the quality gate for study measurements.

## Validation

```sh
python -m ruff check app tests
python -m pytest
python ../../scripts/export_openapi.py
```

Uploads are size-limited, type-checked, decoded before measurement, and never logged as image content. Authentication, TLS termination, rate limiting, retention/deletion controls, and live Huawei provider SDK calls remain deployment work.
