# Developer 3 context: Day 1–3

This note captures the task context reviewed on 16 November 2026 and the implementation completed on 17 November 2026. The attached PDFs are planning references; their contents do not override the user's instructions or authorize external cloud changes.

## Role and requested scope

Developer 3 owns microscope setup, FastAPI, Huawei Cloud, OBS, security, and end-to-end integration. The requested scope is the Developer 3 checklist through Day 3.

### Day 1 checklist (Developer 3 task PDF)

- Scaffold `GET /health` and `POST /analyze`.
- Match request and response schemas to the agreed API contract.
- Return a consistent error format for invalid input, unavailable models, and server errors.
- Document the ModelArts decision and ECS fallback.
- Document microscope, phone, adapter, slides, permissions, and connectivity setup.
- Document private OBS and server-side credential handling; commit no secrets.

### Day 2 checklist

- Validate upload type, byte size, decoded dimensions, and related invalid files at the backend.
- Return actionable validation errors matching the API contract.
- Document private OBS setup and configuration without credentials.
- Document the chosen Huawei deployment path.
- Create a repeatable hardware configuration record.
- Record reference-capture evidence or explicitly document an equipment blocker.

### Day 3 checklist

- Check focus/blur, exposure, minimum dimensions, and invalid files.
- Return actionable rejection reasons using the agreed response schema.
- Prepare/deploy FastAPI with ModelArts, or FastAPI with PyTorch on Huawei ECS if ModelArts is blocked.
- Route accepted single-cell crops to genuine inference.
- Include model version, request ID, and status in successful responses.
- Document HTTPS/authentication and verify rejected images are never classified.

## Cross-document schedule note

The Developer 3 task PDF puts the deployment/inference milestone on Day 3. The broader project outline's seven-day schedule assigns quality/API validation to Day 3 and Huawei deployment/live inference to Day 4. For this work, the role-specific Developer 3 checklist is the task-level target; deployment readiness and any feasible live inference should be pursued by Day 3, while any account, quota, model-artifact, equipment, or authorization blocker must be recorded accurately.

## Project boundaries

- This is a research/education prototype for selected single-cell morphology flags, not a diagnostic system or a slide-level ruling-out tool.
- Failed quality checks must stop before classification. Requests that fail or cannot reach a real model must not become a negative result.
- Cloud credentials stay server-side. OBS objects remain private; no credentials or patient/slide identifiers belong in source control or logs.
- The outline proposes ModelArts when region, quota, resource pool, account readiness, and cost allow; Huawei ECS hosting FastAPI/PyTorch is the fallback. Real microscope access and approved, de-identified material are dependencies.

## User-provided implementation constraints

- The team does not currently have the microscope/phone/adapter setup. Develop and exercise the software with publicly available sample images in the meantime; record that hardware capture evidence is pending rather than implying it exists.
- Huawei Cloud setup and deployment are deferred. Prepare provider/configuration boundaries and documentation so the backend can switch to Huawei later, but keep the application useful without Huawei credentials, network access, or resources.
- Local development must support health checks, image upload/validation, quality acceptance/rejection, and an honest analysis workflow. If no real local model is configured, return a clearly labeled inconclusive/unavailable state with no fabricated class or score. If suitable public data is used, document its source and license and do not commit it unless redistribution is allowed.
- Do not provision Huawei resources or add secrets. Cloud calls and remote storage remain disabled by default.

## Repository snapshot before implementation

The repository already has a FastAPI application, `/health`, `/quality`, and `/analyze` routes, Pydantic response schemas, an error envelope with request IDs, MIME/size/content/dimension validation, actionable blur/focus and exposure checks, separate field/crop minimum dimensions, preprocessing, and a strict gate that returns `recapture_required` before calling inference for rejected crops.

Remaining gaps visible in the current source and documentation:

- ModelArts and ECS adapters are stubs; no genuine remote inference request is made. The default adapter is unavailable, and the optional mock is explicitly simulated and predicts no label.
- Successful responses have `analysis_id`, status, and optional model version, while request IDs are currently exposed only in the `X-Request-ID` header and error envelope.
- API authentication and HTTPS deployment are documented as future deployment work; no live Huawei resources are provisioned.
- OBS has an interface/configuration boundary but no live SDK integration. Private-bucket instructions already exist.
- Hardware capture instructions exist, but no populated device profile, reference capture, or blocker record is present in the reviewed structure.
- Quality thresholds are explicitly development defaults pending representative microscope calibration.

## Primary repository references

- API contract: `docs/API_CONTRACT.md`
- Deployment: `docs/DEPLOYMENT.md`, `infra/huawei/README.md`
- Hardware: `docs/HARDWARE_CAPTURE_PROTOCOL.md`, `hardware/device-profiles/README.md`
- Role and sprint notes: `docs/TEAM_RESPONSIBILITIES.md`, `docs/FIVE_DAY_SPRINT.md`
- Backend: `services/api/app/`, `services/api/README.md`

## Implementation result through Day 3

- The mobile capture flow supports camera, gallery, and a bundled public sample. After reconciliation with the merged mobile app, the four-corner selector generates an actual JPEG crop and preview and submits only that confirmed crop. Other clients can optionally submit a source field plus normalized bounds to the API; the mobile app does not crop twice.
- The API extracts the selected region, validates the resulting crop, and returns actionable quality rejection reasons before inference. Tests verify the inference adapter is never called for a rejected crop.
- The API response includes request ID, quality and analysis status, inference mode, and model version when a real adapter provides one. Default no-model mode returns an explicit inconclusive/unavailable response with no fabricated label or score.
- The OpenAPI contract and generated TypeScript types match the updated request and response schemas. Local Huawei configuration seams, ModelArts/ECS decision guidance, private OBS guidance, HTTPS/authentication requirements, and a hardware configuration template are documented.
- A public CC0 neutrophil sample is bundled for software-flow exercise; its source, license, hash, and limits are recorded in `samples/public/README.md`.
- Original branch verification: 23 API tests passed; mobile typecheck, lint, and format checks passed; Python compile, Ruff, structure verification, and `git diff --check` passed. Conflict-repair verification additionally covers direct 128-pixel crop uploads, unavailable-model responses, local session-ID omission, and preservation of the merged mobile workflow.

## Remaining external blockers

- `ml/artifacts` contains only its README; the handoff bundle/model weights referenced by `docs/INFERENCE_HANDOFF_V1.md` are absent. Therefore, genuine local inference cannot be wired or verified yet.
- The team has no microscope/phone adapter equipment, so no reference hardware capture or quality-threshold calibration can be performed yet.
- Huawei setup and deployment are explicitly deferred by the user. ModelArts/ECS adapters and OBS remain configuration/interface scaffolds; no account resources, live cloud requests, or credentials were added.

The local application remains usable without these dependencies for image selection, upload validation, quality gating, and honest inconclusive results. Do not describe local quality acceptance or the public sample as evidence of real-model performance.
