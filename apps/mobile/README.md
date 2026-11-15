# HemoScope AI mobile app

Android-first Expo client for research microscope capture, image-quality review, manual cell cropping, scoped results and local metadata history. It does not diagnose or rule out disease.

## Run on Android

From the repository root in PowerShell:

```powershell
npm ci
Copy-Item apps/mobile/.env.example apps/mobile/.env
npm run mobile:start
```

Use an Expo Go client matching the installed Expo SDK on the target Android phone, connect both devices to the same trusted network and scan the QR code. The project pins Expo SDK 57 and compatible native dependencies. Camera testing requires a physical phone. On permission denial, use the in-app settings link or Android app permissions; gallery import is available independently of camera permission.

For live integration set `EXPO_PUBLIC_API_MODE=real` and `EXPO_PUBLIC_API_BASE_URL=https://YOUR_BACKEND` in the local `.env`, then restart Metro. For local development only, use the computer's LAN address and port 8000; localhost on a phone refers to the phone. Backend source is currently absent in this working tree; obtain a running endpoint from Developer 3.

For development without the backend, set `EXPO_PUBLIC_API_MODE=mock`, restart Metro, and use Settings to choose a scenario. A banner identifies mock quality measurements and results on every screen. Fixtures do not inspect the image. Production builds ignore mock mode, and failed live requests never fall back to fixtures.

## Flow

Capture/import JPEG, PNG or WebP (up to 10 MB) → review field → quality check → drag/resize a single-cell selection → preview the actual crop → explicitly confirm a complete cell → check crop quality and analyze → result/history. Each crop creates a new cached JPEG; the original field remains available for replacement. Crop geometry uses original image pixels and accounts for displayed aspect ratio. A visual cell check still requires the user; no automatic cell detector is implemented.

Results include recapture required, inconclusive, review required, analysis complete and error. Scores are raw values, not patient risk. Metadata history stores up to 100 local records and no image URI, patient identifier or image content. Clear history in Settings removes metadata; temporary capture/crop files remain in app-managed cache and follow OS/app cache cleanup.

## Checks and build

```powershell
npm run mobile:test
npm run mobile:typecheck
npm run mobile:lint
cd apps/mobile
npx expo export --platform android --output-dir ../../dist/mobile
```

The export validates the production JS/Hermes bundle and assets; it is not an installable APK. On Windows, if Hermes cannot write the sandbox temporary directory, point TEMP and TMP for that shell to a writable directory before exporting.

To produce/install a native release with Android SDK, a compatible JDK, and an attached target device:

```powershell
cd apps/mobile
npx expo run:android --variant release
```

This generates the native project and invokes Gradle; review signing configuration before distributing outside the development team. It needs native build dependencies and may download them. The usual Gradle release outputs are under `android/app/build/outputs/apk/release/`; verify the actual output and signing before recording an installable build as complete. No native APK build or target-phone installation has been verified in this catch-up.

See `tests/README.md` for device regressions and `../../docs/DEVELOPER_2_HANDOFF.md` for checkpoint statuses and PR descriptions.

## UI preview

The supplied UI and logos are implemented across the app. For browser layout checks, use `npm --workspace @hemoscope/mobile run web` with development mock mode. Web preview does not substitute for Android camera/permission or live upload testing. Supplied original brand files are in `assets/brand`; mock history remains explicitly labeled and no sample research records are seeded.
