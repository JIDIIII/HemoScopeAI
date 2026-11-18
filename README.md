# HemoScope AI

HemoScope AI is an Android-first research prototype for guided blood-smear imaging through an existing laboratory microscope. It supports field import/capture, image-quality checks, manual single-cell crop confirmation, and local research inference using an optional packaged model. The API has a portable Docker image and prepared Render Free/OCI Always Free hosting profiles; Huawei-hosted inference remains a later deployment path and is not configured in this repository.

## Research-use disclaimer

This software is for educational and research demonstration only. It is not a medical diagnostic device. It does not diagnose leukemia, rule out disease, estimate patient risk, or recommend treatment. A selected cell or field does not represent an entire slide. Any concerning finding requires qualified review.

Use only authorized, de-identified teaching or research material. Do not upload patient names, slide labels, requisition forms, or other identifying information. Dataset files and model checkpoints are local, ignored artifacts and are not distributed through Git. Saved validation metrics are research-development evidence only; they are not clinical performance evidence.

## Architecture

~~~mermaid
flowchart LR
  phone[Android phone and microscope adapter]
  mobile[Expo React Native app]
  quality[FastAPI image validation and quality gate]
  crop[Manual single-cell crop]
  inference[Inference adapter]
  cloud[Huawei ModelArts or ECS]
  obs[Private Huawei OBS]
  history[Local research session metadata]
  phone --> mobile
  mobile --> quality
  quality -->|accepted field| crop
  crop -->|confirmed crop only| inference
  inference --> cloud
  cloud --> obs
  mobile --> history
~~~

The app owns camera and gallery access, preview, navigation, API calls, and local history. FastAPI owns upload validation, quality checks, error handling, and inference orchestration. The ML package owns data loading, subject-level splits, preprocessing, MobileNetV3-Small training, evaluation, and local checkpoint inference. Huawei adapters stay on the server side.

## Technology

- Mobile: React Native, Expo SDK 57, TypeScript, Expo Router, Expo Camera, Expo Image Picker, AsyncStorage. The first scaffold targets Android; iOS can be enabled after its device and permission flow is reviewed.
- API: Python 3.11+, FastAPI, Pydantic, Uvicorn, Pillow, OpenCV, NumPy, Pytest, Ruff.
- ML: PyTorch, Torchvision, MobileNetV3-Small, Scikit-learn, OpenCV.
- Hosting and identity: Render Free with Supabase Free Auth is the prepared no-card, zero-dollar prototype path; OCI Always Free is a higher-capacity option with card-verification and idle-reclamation caveats.
- CI and formatting: GitHub Actions, ESLint, Prettier, Ruff, Pytest, TypeScript.

SDK 57 is selected because Expo currently pairs it with React Native 0.86 and React 19.2.3, and its camera and image picker packages are supported by Expo Go on physical devices. Use the Expo Go version matching the project SDK.

## Repository layout

~~~text
apps/mobile/       Expo app, screens, API client, and local session store
services/api/      FastAPI routes, Pydantic schemas, quality and cloud boundaries
ml/                Dataset checks, preprocessing, training, evaluation, inference
packages/contracts/ OpenAPI contract snapshot
hardware/          Adapter and repeatable capture protocol
infra/             hosting, Huawei, and Docker deployment notes
docs/              Architecture, safety, setup, team, and sprint documents
scripts/            Contract generation and structure verification
~~~

## Prerequisites

- Node.js 22.13 or newer and npm.
- Python 3.11 or newer.
- Android phone with the matching Expo Go client for camera testing.
- A development computer and phone on the same trusted Wi-Fi network for API testing from a physical device.
- Microscope, adapter, and approved slides are needed only for hardware validation.

## Start the backend

~~~sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e "services/api[dev]"
cp services/api/.env.example services/api/.env
cd services/api
python -m uvicorn app.main:app --reload --host 0.0.0.0
~~~

The service listens on port 8000. Open /health and /docs on the development computer. To connect a physical Android phone, set EXPO_PUBLIC_API_BASE_URL in apps/mobile/.env to http://COMPUTER_LAN_IP:8000 and keep both devices on the same Wi-Fi. Allow port 8000 through the local firewall.

## Start the mobile app

In another terminal from the repository root:

~~~sh
npm ci
cp apps/mobile/.env.example apps/mobile/.env
npm run mobile:start
~~~

Scan the Expo development QR code with the matching Expo Go app. For an emulator, use the emulator's host bridge address instead of localhost where required by the platform.

## Validation commands

~~~sh
python -m ruff check --config services/api/pyproject.toml services/api/app services/api/tests
python -m pytest services/api/tests
npm run mobile:typecheck
npm run mobile:lint
python3 scripts/export_openapi.py
python3 scripts/generate_api_types.py
python3 scripts/verify_structure.py
~~~

The API quality suite uses generated test images and runs without a microscope, dataset, GPU, trained checkpoint, or Huawei account. For lightweight ML dataset/split tests, install `python -m pip install -e "ml/[dev]"` and run `cd ml && python -m pytest`; this does not install PyTorch or download data.

## Environment configuration

Copy services/api/.env.example and apps/mobile/.env.example to local .env files. The examples contain placeholders only. Hosted builds use the same Supabase project URL and publishable key in the app and API; keep public sign-ups disabled and do not bundle any Supabase secret or service-role key. Huawei credentials belong only in a protected server environment and must never be bundled into the mobile app. Quality limits in the API example are development defaults and require calibration on representative microscope images.

## Three-developer responsibilities

- Developer 1, AI/ML: ml/, data audit, subject-separated splits, preprocessing, training, evaluation, inference package, and model card.
- Developer 2, Mobile: apps/mobile/, capture and import, crop UI, quality feedback, result states, and local research history.
- Developer 3, Cloud/Hardware: services/api/, infra/, hardware/, Huawei deployment, security, and integration.

Suggested local branches are feature/ai-pipeline, feature/mobile-app, and feature/backend-cloud. These are recommendations only; no remote branches are created. Shared Pydantic contract changes must be exported to packages/contracts/openapi.json and the generated mobile API types in the same change.

## Hosting and Huawei Cloud overview

For the hard-$0 constraint, use the Render Free Blueprint in `infra/hosting/render.yaml` with Supabase Free Auth. It supports the no-model preview and sleeps when idle; OCI Always Free offers more memory if card verification and VM reclamation risk are acceptable. The hosted service is not live yet, and the frozen model bundle is not present in this checkout; see [deployment options](infra/hosting/README.md).

The future Huawei path is the same portable FastAPI container on Huawei ECS or FastAPI calling a verified Huawei ModelArts endpoint, with server-side credentials. Use a private OBS bucket only if storage is later required. Current provider classes are interface scaffolds and do not yet call Huawei APIs. See docs/DEPLOYMENT.md before enabling a cloud service. This repository does not provision billable resources.

## Five-day roadmap

The requested five-day plan is in docs/FIVE_DAY_SPRINT.md. It covers foundation, baseline preparation, quality and cloud integration, phone-to-cloud integration, then validation and handoff. The supplied project outline uses a seven-day horizon; this repository follows the requested five-day checklist and does not claim that later milestones are complete.

## Current implementation status

Implemented: Expo navigation shell, research disclaimer, setup instructions, camera and gallery permission paths, image preview, API-backed quality review, local non-identifying metadata history, optional Supabase email/password sign-in and API token validation, FastAPI health/quality/analyze/session routes, structured errors, development-only simulated response, image quality module, ML training/evaluation interfaces, generated API contracts, portable Dockerfile, CI, and project documentation.

Mobile catch-up: drag-and-resize crop generation, explicit crop preview/confirmation, crop quality gating, analysis/result handling, opt-in labeled development fixtures, and local result history are implemented. See docs/DEVELOPER_2_HANDOFF.md for PR descriptions, validation evidence, and pending checkpoints.

Still pending: hosting account/budget setup, a Supabase Auth project and issued accounts, public service/TLS configuration, the ignored model bundle required for real inference (it is not present in this checkout), live ModelArts/ECS inference, an OBS SDK client, rate limiting and retention/deletion controls, calibrated microscopy thresholds, native APK distribution, and physical microscope/phone validation. The authentication flow is implemented but remains disabled by default until its Supabase project is configured. The bundled public sample supports software-flow checks only; it is not representative hardware evidence or a model-accuracy sample. A failed real request never falls back to simulated inference.
