# Development setup

## Required tools

- Node.js 22.13 or newer with npm.
- Python 3.11 or newer.
- Expo Go matching the mobile project's Expo SDK for camera tests on a physical Android phone.
- Git for local branching and GitHub Actions integration.

## Backend

~~~sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e "services/api[dev]"
cp services/api/.env.example services/api/.env
cd services/api
python -m uvicorn app.main:app --reload --host 0.0.0.0
~~~

GET /health returns service and model availability. API documentation is exposed by FastAPI at /docs. The backend defaults to no inference model and does not require a dataset or GPU. It enforces a request byte limit and a configurable decoded-pixel ceiling before calculating quality measurements.

## Mobile

From the repository root, in a second terminal:

~~~sh
npm ci
cp apps/mobile/.env.example apps/mobile/.env
npm run mobile:start
~~~

For a real phone, find the computer's private LAN IPv4 address and set EXPO_PUBLIC_API_BASE_URL=http://LAN_IP:8000 in apps/mobile/.env. Both devices need the same trusted network, and the computer firewall must permit port 8000. Never expose the development server to an untrusted public network.

## Checks

~~~sh
python -m ruff check --config services/api/pyproject.toml services/api/app services/api/tests
python -m pytest services/api/tests
npm run mobile:typecheck
npm run mobile:lint
python3 scripts/export_openapi.py
python3 scripts/generate_api_types.py
python3 scripts/verify_structure.py
~~~

For the ML dataset-integrity and subject-split tests, install `python -m pip install -e "ml/[dev]"`, then run `cd ml && python -m pytest`. This does not install PyTorch or retrieve a dataset.

## Environment files

Local .env files are ignored by Git. The example templates contain only blank credential placeholders. Use the backend environment for Huawei configuration. Expo EXPO_PUBLIC_ values are bundled into the app and must contain no secrets.

## Current limits

The camera and gallery paths can acquire an image, but a drag-and-resize cell crop is still TODO. The quality thresholds are adjustable development defaults. The cloud adapter classes do not yet implement provider calls. The local scaffold therefore cannot complete a genuine phone-to-Huawei inference demonstration.
