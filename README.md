# HemoScope AI

HemoScope AI is an Android-first research prototype for guided blood-smear imaging through an existing laboratory microscope. It helps a researcher capture or import a microscope field, check image quality, manually choose one cell, and submit a confirmed crop to a backend that can later connect to Huawei Cloud inference.

## Research-use disclaimer

This software is for educational and research demonstration only. It is not a medical diagnostic device. It does not diagnose leukemia, rule out disease, estimate patient risk, or recommend treatment. A selected cell or field does not represent an entire slide. Any concerning finding requires qualified review.

Use only authorized, de-identified teaching or research material. Do not upload patient names, slide labels, requisition forms, or other identifying information. No model weights, dataset files, clinical performance figures, or real inference responses are included in this scaffold.

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
- Cloud target: Huawei OBS, ModelArts where available, or ECS as inference fallback.
- CI and formatting: GitHub Actions, ESLint, Prettier, Ruff, Pytest, TypeScript.

SDK 57 is selected because Expo currently pairs it with React Native 0.86 and React 19.2.3, and its camera and image picker packages are supported by Expo Go on physical devices. Use the Expo Go version matching the project SDK.

## Repository layout

~~~text
apps/mobile/       Expo app, screens, API client, and local session store
services/api/      FastAPI routes, Pydantic schemas, quality and cloud boundaries
ml/                Dataset checks, preprocessing, training, evaluation, inference
packages/contracts/ OpenAPI contract snapshot
hardware/          Adapter and repeatable capture protocol
infra/             Huawei and Docker deployment notes
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

Copy services/api/.env.example and apps/mobile/.env.example to local .env files. The examples contain placeholders only. Huawei credentials belong only in a protected server environment and must never be bundled into the mobile app. Quality limits in the API example are development defaults and require calibration on representative microscope images.

## Three-developer responsibilities

- Developer 1, AI/ML: ml/, data audit, subject-separated splits, preprocessing, training, evaluation, inference package, and model card.
- Developer 2, Mobile: apps/mobile/, capture and import, crop UI, quality feedback, result states, and local research history.
- Developer 3, Cloud/Hardware: services/api/, infra/, hardware/, Huawei deployment, security, and integration.

Suggested local branches are feature/ai-pipeline, feature/mobile-app, and feature/backend-cloud. These are recommendations only; no remote branches are created. Shared Pydantic contract changes must be exported to packages/contracts/openapi.json and the generated mobile API types in the same change.

## Huawei Cloud deployment overview

The preferred path is FastAPI over HTTPS with server-side Huawei IAM credentials, a private OBS bucket, and ModelArts real-time inference when region, account, quota, and cost allow. Use FastAPI plus PyTorch on Huawei ECS when ModelArts is unavailable. Current provider classes are interface scaffolds and do not yet call Huawei APIs. See docs/DEPLOYMENT.md before enabling a cloud service. This repository does not provision billable resources.

## Five-day roadmap

The requested five-day plan is in docs/FIVE_DAY_SPRINT.md. It covers foundation, baseline preparation, quality and cloud integration, phone-to-cloud integration, then validation and handoff. The supplied project outline uses a seven-day horizon; this repository follows the requested five-day checklist and does not claim that later milestones are complete.

## Current implementation status

Implemented: Expo navigation shell, research disclaimer, setup instructions, camera and gallery permission paths, image preview, API-backed quality review, local non-identifying metadata history, FastAPI health/quality/analyze/session routes, structured errors, development-only simulated response, image quality module, ML training/evaluation interfaces, generated API contracts, Dockerfile, CI, and project documentation.

Not implemented: drag-and-resize crop generation, a trained model, live ModelArts/ECS inference, an OBS SDK client, authentication, server-side history, calibrated microscopy thresholds, or physical-device/hardware validation. Analysis stays disabled in the mobile UI until a confirmed crop is produced. The API defaults to model_unavailable and never fabricates a real prediction.
