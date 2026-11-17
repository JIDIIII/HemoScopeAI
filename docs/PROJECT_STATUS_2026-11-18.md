# HemoScope AI project checklist status — 18 November 2026

This checklist follows the five-day plan in the local project outline. The outline is a planning document; completion below is based on current source files, generated artifacts, local checks, and emulator evidence supplied by the user. **Complete** means the locally achievable item has evidence. **Partial** means a meaningful part is done but the stated target or evidence is missing. **Pending** means the required work has not been done. Local development is not evidence of a live cloud service, physical microscope workflow, or clinical performance.

## Developer 1 — AI / ML

| Day | Original checklist item | Status | Evidence and limit |
| --- | --- | --- | --- |
| 1 | Confirm C-NMC access/permitted use; verify labels, subject IDs, file counts and class balance. | **Partial** | C-NMC CC BY 3.0 terms and attribution, NIH/NLM and BCCD dataset notices, labels, counts, class balance and grouping are recorded in the dataset reviews. Team-specific institutional oversight/authorization and C-NMC download provenance are not evidenced in this checkout. |
| 1 | Create a fixed-seed subject-separated train/validation/test manifest; check duplicate or leaking subjects. | **Complete for grouping-v1 policy** | Frozen split SHA-256 `38a8b633…564a` assigns all reviewed dependency groups to one partition and keeps 208 exact duplicate copies excluded. The 56 groups are conservative image-dependency groups, not verified independent patients; source identity remains uncertain. |
| 1 | Set up training environment and baseline notebook with fixed image size/preprocessing. | **Complete** | ML environment, notebook, versioned configs and 224×224 RGB normalization metadata exist. The original baseline remains preserved. |
| 1 | Agree model input/output fields and validation metrics with mobile/cloud owners. | **Complete for local contract** | `/analyze` contract, OpenAPI/mobile types and local API integration expose status, ALL score, policy/model versions and warnings. Live Huawei behavior is not verified. |
| 2 | Train lightweight MobileNetV3-Small baseline on approved subject-separated subset. | **Partial** | Four bounded candidates exist on the frozen grouped split. Formal project-level dataset oversight is not recorded, so the “approved” condition cannot be confirmed from repository evidence. |
| 2 | Record validation sensitivity, specificity, weighted F1 and confusion matrix; keep test untouched. | **Complete with limitation** | Four candidates were compared on the same validation partition. The selected candidate’s grouped internal test was evaluated only after model/policy selection. An earlier baseline test result had already informed data investigation; the revised test is not a pristine independent cohort. See [final candidate evaluation](FINAL_CANDIDATE_EVALUATION_V1.md). |
| 2 | Build reusable preprocessing/inference wrapper that matches training transforms. | **Complete** | Standalone inference package, preprocessing metadata, API adapter and handoff bundle are present. Local CPU model/API check is covered by tests. |
| 2 | Save checkpoint, configuration, seed, split and dependency versions. | **Complete for saved experiments** | Each run has a checkpoint, configuration, seed, split manifest and model metadata. Checkpoint and split hashes are recorded; generated checkpoints remain ignored. |
| 3 | Package baseline/preprocessing and confirm a valid crop returns a real score. | **Complete locally** | Local bundle self-test and API adapter use the selected checkpoint. User-provided emulator/API flow reached a real local result. No Huawei endpoint was used. |
| 3 | Choose a conservative threshold/inconclusive interval using validation only. | **Complete as provisional Option B** | User-selected 0.30/0.70 policy is versioned and bound to the exact grouped low-learning-rate checkpoint. It was not changed based on the grouped test. It is not calibrated clinical probability. |
| 3 | Record model version/hash and state scores are uncalibrated. | **Complete** | Model, checkpoint, split, preprocessing and policy versions/hashes are recorded in metadata, handoff and API response. |
| 3 | Call the model only after quality acceptance and manual single-cell crop confirmation. | **Complete in local code** | API route gates inference on accepted quality and crop confirmation; targeted route tests cover rejection and errors. Automatic localization is not enabled. |
| 4 | Evaluate available phone crops separately and report counts. | **Partial** | A separate generic-WBC detector check was run on 165 NIH/NLM smartphone microscope fields. No independently labeled phone crops with ALL/HEM outcomes are available to evaluate the classifier. |
| 4 | Compare source-domain and phone-crop behavior; record domain shift, uncertainty and failures. | **Partial** | The detector’s smartphone WBC check yielded 0/51 WBC matches at IoU 0.50 and is documented. It is a malaria WBC-localization check, not leukemia classifier validation. Classifier target-device domain shift remains unknown. |
| 4 | Check deployed model/preprocessing hashes against frozen candidate. | **Partial** | Local handoff bundle hashes and CPU self-test were verified. There is no deployed Huawei model to compare. |
| 5 | Finalize held-out subject-separated metrics/plots with denominators; do not tune on test. | **Complete for grouped internal evaluation** | The candidate was selected from validation; grouped internal test evaluated once afterward. Metrics, denominators, confusion matrix plot and limitations are in the evaluation report. The earlier test-informed grouping limits independence; no test tuning occurred. |
| 5 | Prepare model card with provenance, split method, thresholds, uncertainty and failure modes. | **Complete for the research candidate** | The preliminary handoff model card plus [final evaluation report](FINAL_CANDIDATE_EVALUATION_V1.md) record provenance, split limits, thresholds, metrics, failures and intended use. |
| 5 | Freeze/hash model, preprocessing config and inference version. | **Complete as a provisional local candidate** | Candidate `hemoscope-mobilenetv3-small-grouped-lowlr-v1`, checkpoint SHA-256 `58b80cd5…2b98`, preprocessing and inference/policy version are pinned. This is a research-software freeze, not a clinical release or deployed model freeze. |
| 5 | State evidence supports research demonstration, not clinical performance. | **Complete** | Model card, app notices, API warning and README state research/educational use only and require qualified review. |

## Developer 2 — Mobile

| Day | Original checklist item | Status | Evidence and limit |
| --- | --- | --- | --- |
| 1 | Initialize Expo project and confirm Android run path on target phone. | **Partial** | Expo and Android emulator workflow are present and user screenshots show it running. A physical target phone was not used. |
| 1 | Scaffold welcome/research disclaimer, navigation and one capture entry point. | **Complete locally** | Screens and navigation are implemented; automated workflow checks are listed below. |
| 1 | Build camera/gallery screen with permission, loading and invalid-file states. | **Complete locally** | Mobile source and workflow tests cover image selection and error paths. Emulator evidence confirms the app opens. Physical camera behavior remains unverified. |
| 1 | Create API client and clearly identified development mock for `/health` and `/analyze`. | **Complete locally** | API client, generated contract types and development mock/local configuration are present. The user also confirmed local API reachability from the emulator browser. |
| 2 | Complete camera capture and gallery import on target Android phone with full-field preview. | **Partial** | Emulator image import/preview is available. No physical phone camera or target-device gallery run was supplied. |
| 2 | Add manual drag/resize crop and confirm one complete white blood cell. | **Complete in emulator workflow** | Manual crop/review flow is implemented and the user supplied emulator walkthrough evidence. No microscope-captured field was used. |
| 2 | Wire capture, preview, crop and result screens to agreed API payload. | **Complete locally** | App submits confirmed crop to the local API contract; emulator/API workflow evidence is available. |
| 2 | Handle permission denial, unsupported format and cancel/retry without losing image. | **Complete in code/tests** | Error and retry paths are implemented and covered by mobile workflow tests. Physical-device behavior remains unverified. |
| 3 | Add quality review states and specific recapture guidance. | **Complete locally** | Review screen covers focus, exposure, dimensions and invalid/rejected image guidance. |
| 3 | Connect real API and display accepted, rejected, inconclusive, review-required and error states. | **Complete locally** | Contract types/result mapping are implemented; user screenshots show quality and result states. Live cloud results remain pending. |
| 3 | Preserve original field while user confirms/replaces crop. | **Complete in code** | Capture/review/crop navigation preserves the selected source image and lets the user return or replace it. |
| 3 | Handle offline, timeout and server errors without crash or negative result. | **Complete in code/tests** | The app has explicit error states; the earlier emulator connection failure appeared as an error, not a classification. Local tests cover error handling. |
| 4 | Run capture→quality→crop→upload→result on physical phone. | **Pending** | The available evidence is Android emulator only. A physical Android phone and microscope adapter are not available in this checkout. |
| 4 | Add local non-identifying history with timestamp, local image ID, quality and model version. | **Complete in emulator workflow** | Local history and saved-result UI are implemented; the user supplied a “Research Session Saved” emulator screenshot. No patient identifiers should be entered. |
| 4 | Verify research notice and qualified-review wording on every result state. | **Complete in source/local review** | Result and disclaimer copy is present in the app. Physical target-device review is not performed. |
| 4 | Exercise retake, inconclusive, offline, timeout, invalid-file and server-error paths. | **Complete in automated/local checks** | The mobile workflow tests cover the supported states. Physical-network and cloud failure behavior remain unverified. |
| 5 | Build/install Android prototype on target phone; keep backup build if available. | **Partial** | Prior status records a local ARM64 emulator build/install. The APK uses development signing; physical-phone installation and a backup phone build are not evidenced. |
| 5 | Run final regressions for capture, crop, quality, result, history and errors. | **Complete for local/emulator scope** | Current typecheck, lint and mobile tests are rerun for this status pass; physical camera regression remains pending. |
| 5 | Polish instructions and ensure no screen implies diagnosis or disease exclusion. | **Complete locally** | Screens state research use only, describe inconclusive/review states and do not show the hidden raw label as a patient diagnosis. |
| 5 | Prepare 3-minute demo and record real app with live endpoint. | **Pending** | No recording or live endpoint is present; the local emulator is suitable for a software-only demo when labeled accurately. |

## Developer 3 — Cloud and hardware

| Day | Original checklist item | Status | Evidence and limit |
| --- | --- | --- | --- |
| 1 | Confirm lab permission, authorized de-identified slides, microscope, phone, adapter, connectivity and equipment owner. | **Pending** | No completed lab/access/equipment record or physical capture is present. |
| 1 | Check Huawei region/IAM/quota/billing and choose ModelArts or ECS fallback. | **Pending** | No Huawei account/resource evidence is available. This is deployment/access work and remains out of scope here. |
| 1 | Scaffold FastAPI `/health` and `/analyze` and agree request/response/error contract. | **Complete locally** | FastAPI routes, schemas, OpenAPI and API contract are present and tested locally. |
| 1 | Plan private OBS and server-side credentials; keep secrets out of mobile app. | **Partial** | Private-storage/security guidance and environment examples exist. No private bucket or live credentials were configured. |
| 2 | Record phone/microscope/objective/eyepiece/adapter/camera settings. | **Pending** | A setup template exists; actual equipment values and reference capture are missing. |
| 2 | Fit adapter and capture reference fields; record alignment/illumination/focus issues. | **Pending** | Requires physical hardware and authorized slides. |
| 2 | Add backend file type, size and dimension validation with clear errors. | **Complete locally** | Upload validation and structured error codes are implemented and covered by API tests. |
| 2 | Create/verify private OBS and prepare Huawei path. | **Pending** | No live bucket, account access, endpoint or cloud resource was created. |
| 3 | Implement blur/focus, exposure and minimum-dimension checks with reasons/instructions. | **Complete locally, calibration pending** | Local quality checks and rejection guidance exist. Thresholds still need calibration on representative microscope captures. |
| 3 | Deploy FastAPI with ModelArts or ECS fallback. | **Pending — deployment** | Explicitly excluded from this work. |
| 3 | Route accepted crops to real model and return status/score/version/request ID. | **Complete locally** | Local API integration uses the packaged model and emits the agreed response fields. Huawei-hosted inference is not present. |
| 3 | Secure endpoint using HTTPS and scoped server credentials; verify rejection gates. | **Partial** | Local rejection gates are tested. HTTPS, IAM-scoped secrets and remote authentication require deployment and are not configured. |
| 4 | Run repeatable microscope/phone captures; record usable rate and limitations. | **Pending** | No physical capture set or equipment record is available. |
| 4 | Verify endpoint auth, private OBS, and logs without image/identity data. | **Pending** | No deployed endpoint or private OBS exists. |
| 4 | Measure request latency/failures on target network. | **Pending** | Only local/emulator connectivity was checked; no target-network measurement exists. |
| 4 | Fix integration blockers and confirm live-model response. | **Partial** | Local mobile/API/model path works. Live cloud path and physical capture are unverified. |
| 5 | Verify live endpoint, access, storage, latency and real inference. | **Pending — deployment** | No cloud endpoint/resources were provisioned or checked. |
| 5 | Document architecture, API, deployment steps, hardware setup and capture protocol. | **Complete as local documentation** | Architecture, contract, deployment guide and hardware/capture templates exist; actual setup values remain pending. |
| 5 | Review cloud spend, billing alerts, retention and resource cleanup; record final cloud state. | **Pending — deployment** | Requires cloud account ownership and live resources. |
| 5 | Capture hardware/cloud evidence without credentials or identifiers. | **Pending** | No physical/cloud evidence exists. |

## Final handoff checklist

| Deliverable | Status | Evidence |
| --- | --- | --- |
| Tested Android build and target-phone demo steps | **Partial** | Emulator build/workflow evidence exists; physical target phone and recording are pending. |
| Versioned model, preprocessing, training/evaluation files and measured metrics | **Complete for local research candidate** | Checkpoint/config/metadata, frozen split, policy, model card and evaluation report are recorded locally. Dataset and weights are not committed. |
| Live Huawei endpoint proof, architecture, API contract and deployment notes | **Partial** | Architecture/API/deployment documentation exists; live Huawei proof is pending. |
| Hardware setup record, research safety notice, data/model cards and source attribution | **Partial** | Notices/cards and dataset audit are present; hardware record and any external-source evidence remain pending. |
| Three-minute demo recording or ready-to-run presentation flow | **Partial** | A local emulator walkthrough can be run; no three-minute recording or live endpoint exists. |

## Deployment-only items left to the project owner

1. Confirm Huawei account owner, region, IAM roles, quota, billing controls and the ModelArts/ECS decision.
2. Provision/configure the inference service and private OBS storage; keep credentials server-side and scoped.
3. Configure HTTPS, authentication, retention, privacy-safe logging, monitoring and budget alerts.
4. Deploy the exact frozen checkpoint/preprocessing/policy, then verify its hashes against the local candidate.
5. Run live API security/error/latency checks and record the cloud resource state and cleanup steps.

Physical lab/phone access is a separate external blocker, not a deployment action. It is needed for representative microscope captures, quality-threshold calibration and target-device validation.

## Checks run for this status pass

- `./.venv/bin/python -m ruff check --config services/api/pyproject.toml services/api/app services/api/tests ml/src ml/tests scripts` — passed, all checks clean.
- `git diff --check` — passed, no whitespace errors.
- `./.venv/bin/python scripts/verify_structure.py` — passed; all 24 required paths present and no model weights tracked.
- `./.venv/bin/python -m pytest services/api/tests` — 24 passed. One Starlette/httpx TestClient deprecation warning remains.
- From `ml`: `../.venv/bin/python -m pytest` — 62 passed, one MPS-only training test skipped because MPS is unavailable in this environment.
- `npm run mobile:typecheck`, `npm run mobile:lint`, and `npm run mobile:test` — all passed; 20 mobile tests passed.
- `npm exec --workspace @hemoscope/mobile -- expo export --platform android --output-dir /tmp/hemoscope-android-export` — passed; Android JavaScript bundle exported to `/tmp/hemoscope-android-export`. This is not a signed/installable release APK.
- `./.venv/bin/python ml/artifacts/handoff/hemoscope-inference-handoff-v1/verify_bundle.py --self-test` — passed; 20 bundle checksums, offline CPU forward pass, and decision-policy boundaries verified. The synthetic forward pass is packaging evidence only.
- A local TestClient smoke check reached `/health` and submitted a synthetic image to `/analyze`; the local real-model adapter returned an accepted, complete response with model/policy version and score. This verifies wiring only, not image suitability or model accuracy.
- The grouped candidate's one-time internal test evaluation and the separate NIH/NLM smartphone detector diagnostic are recorded in the linked reports above. The latter failed WBC localization (0/51 matches), so it was not integrated as an automatic cropper.
- Regenerating the OpenAPI snapshot and mobile API types produced no content changes. `git check-ignore -v` confirmed downloaded data, model checkpoints and the project-outline PDF are ignored.

The existing working-tree changes were preserved. Nothing was staged, committed, pushed, merged, deployed, or uploaded to a model/cloud service.
