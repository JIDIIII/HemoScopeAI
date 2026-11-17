# Solo-developer runbook

This runbook covers repo work that can be done without training or tuning. It keeps the local software demo separate from physical hardware and live-cloud evidence.

## 1. Start the API

From the repository root, activate the existing project environment and start the API:

```sh
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --app-dir services/api
```

Open `http://127.0.0.1:8000/health` on the computer. The default provider is `none`; an accepted image then returns an explicit inconclusive/unavailable response.

For local model inference, install the optional dependency and set `HEMOSCOPE_INFERENCE_PROVIDER=local` in `services/api/.env`:

```sh
python -m pip install -e "services/api[local-inference]"
```

The adapter loads the ignored bundle under `ml/artifacts/handoff/hemoscope-inference-handoff-v1`. It runs on CPU, after the API has checked the upload, crop confirmation and crop quality. It does not call Huawei. Stop the server with `Ctrl+C`.

## 2. Start the mobile app

In a second terminal from the repository root:

```sh
npm run mobile:start
```

For the Android Studio emulator, set this in `apps/mobile/.env` before Metro starts:

```text
EXPO_PUBLIC_API_BASE_URL=http://10.0.2.2:8000
```

Reload the app after changing the URL. Import a bundled public sample or a de-identified image in the emulator Photos library. If the photo picker does not show a file in Downloads, copy/import it into Photos first. Follow the app flow: review image, check quality, draw a crop around one complete cell, preview and confirm the crop, then analyze. The emulator does not provide evidence of physical microscope capture.

For a physical phone, use the computer's private LAN IPv4 address instead of `10.0.2.2`, keep both devices on the same trusted network, and allow port 8000 through the computer firewall.

### Build a standalone Android demo APK

The native Android project is generated from the Expo app. From the repository root, build an ARM64 release APK (the configured Pixel emulator and modern Android phones use ARM64):

```sh
cd apps/mobile/android
./gradlew assembleRelease -PreactNativeArchitectures=arm64-v8a
```

The APK is at `apps/mobile/android/app/build/outputs/apk/release/app-release.apk`. Install it on a connected emulator or phone with:

```sh
adb install -r apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

The release APK bundles the JavaScript and opens without Metro. Its API URL is read from `apps/mobile/.env` when building; use `http://10.0.2.2:8000` for the Android emulator, or set the computer's private LAN address before rebuilding for a physical phone. This local demo build uses Android's default debug signing key, so it is not a Play Store release. Physical-phone capture and installation still need separate verification.

## 3. Run software checks

From the repository root:

```sh
source .venv/bin/activate
python -m pytest services/api/tests -q
python -m ruff check --config services/api/pyproject.toml services/api/app services/api/tests ml/src ml/tests scripts
cd ml && ../.venv/bin/python -m pytest -q && cd ..
npm run mobile:typecheck
npm run mobile:lint
npm run mobile:test
python scripts/verify_structure.py
```

`npm run contracts:check` compares generated files with `HEAD`; if you have uncommitted contract changes, a diff may be expected. To verify generation is stable, regenerate OpenAPI and TypeScript types twice and confirm their file hashes are unchanged between runs.

The handoff bundle's offline integrity and packaging check is:

```sh
python ml/artifacts/handoff/hemoscope-inference-handoff-v1/verify_bundle.py --self-test
```

This synthetic CPU check does not measure accuracy or image quality. The local diagnostics are validation-only; do not evaluate the reserved grouped internal test until model and policy choices are frozen. Training and model-setting changes remain separate user-run steps.

## 4. Keep the evidence straight

- Call the current model a provisional research candidate; do not imply it is clinically accurate or externally validated.
- Report local model inference separately from simulated results and Huawei-hosted inference.
- Do not use the public sample, C-NMC validation images, or emulator screenshots as phone-capture accuracy evidence.
- Keep the physical phone/microscope workflow, authorized and labeled phone-crop cohort, cloud endpoint, authentication and privacy controls marked pending until verified. The native APK has been installed and opened in the emulator; physical-phone installation is still pending.

See [the item-level project status](PROJECT_STATUS_2026-11-17.md), [deployment notes](DEPLOYMENT.md), and [the demo checklist](DEMO_CHECKLIST.md).
