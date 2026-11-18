# Developer 2 final mobile handoff - 18 November 2026

Scope: the seven unchecked Developer 2 items in `HemoScope_AI_Detailed_Project_Outline (7).pdf`, pages 2-3. The owner requested emulator testing for now. Physical-phone acceptance remains separate.

## Windows build and run

From the repository root in PowerShell, with Node dependencies installed (`npm ci` if needed):

```powershell
# Explicit development simulation; no backend or model is needed.
$env:EXPO_PUBLIC_API_MODE = 'mock'
npm run mobile:start -- --localhost --port 8083
```

In a second terminal, start the configured Android Studio AVD, then:

```powershell
$adbTool = "$env:LOCALAPPDATA/Android/Sdk/platform-tools/adb.exe"
& $adbTool devices -l
& $adbTool reverse tcp:8083 tcp:8083
& $adbTool shell am start -a android.intent.action.VIEW -d exp://127.0.0.1:8083
```

Use an Expo Go version matching the project's SDK 57. Development mock mode is disabled in production builds. Settings, field review and crop review expose **Demo controls** only in development mock mode. Changing the field-review fixture clears the previous quality result; run the check again before proceeding. Fixture controls are hidden during quality/analysis requests. Simulated timeout is an immediate error after the fixture delay, not a measurement of the real 15-second timeout.

For a real API, stop Metro, set `EXPO_PUBLIC_API_MODE=real`, and set `EXPO_PUBLIC_API_BASE_URL` to the actual endpoint before restarting. Android emulator access to a host API normally uses `http://10.0.2.2:8000`; a phone uses the development computer's reachable LAN address. Settings > Service connection checks health. The local model bundle must actually exist for local inference; do not assume it is included in a Git checkout. Never describe an unavailable or simulated response as real inference.

### Native APK

Install the Android SDK and the JDK supported by this repository's Gradle/Android plugin, and point `JAVA_HOME` and `ANDROID_HOME` to those installations. Do not overwrite existing local paths. From the repository root:

```powershell
$env:EXPO_PUBLIC_API_MODE = 'real'
$env:EXPO_PUBLIC_API_BASE_URL = 'http://10.0.2.2:8000'
Push-Location apps/mobile/android
.\gradlew.bat assembleRelease -PreactNativeArchitectures=x86_64
Pop-Location
& $adbTool install -r apps/mobile/android/app/build/outputs/apk/release/app-release.apk
```

Use the target device's ABI (`adb shell getprop ro.product.cpu.abi`) instead of assuming ARM64; the current emulator is x86_64. For a physical ARM64 phone, build `arm64-v8a` with a phone-reachable endpoint. Release bundles the endpoint at build time, so changing it requires rebuilding. The current Android release configuration uses development signing; it is not a store-signed release. These are build instructions, not evidence of a new native APK build/install in this pass.

## Repeatable three-minute software demo

Prepare before timing: start the emulator and Metro in explicit mock mode, load the app, complete onboarding, select `inconclusive` in Settings > Demo controls. Use the bundled attributed public sample; it is not a leukemia validation image or physical microscope capture. Do not use patient material.

| Time | Action and narration |
| --- | --- |
| 0:00-0:20 | Show the dashboard and research notice. Say: "This is an emulator software demonstration with simulated responses, not clinical or live Huawei inference." |
| 0:20-0:45 | Start New Scan > Try public sample image. Show the full field preview and explain that the source image remains available when replacing a crop. |
| 0:45-1:10 | Run Check image quality. Explain that this response is simulated and passing engineering checks does not establish biological suitability. Continue to Cell Selection. |
| 1:10-1:50 | Drag/resize the selection around one complete visible cell. Preview selected crop, then Confirm Cell Selection. Explain that only the confirmed crop is submitted for analysis in real mode. |
| 1:50-2:15 | Run Check crop quality and analyze. Show the Inconclusive result, simulation label, research notice and Technical Details. State that inconclusive is not a negative finding. |
| 2:15-2:35 | View History; show timestamp, quality state, model/simulation information and local session ID. History stores metadata, not patient identifiers or image content. |
| 2:35-3:00 | Start another sample review, select `recapture_required` in Demo controls, and run the quality check. Show the retake instruction and absence of Continue to Cell Selection. Close with the pending physical-phone and real-endpoint validation. |

If the flow takes longer, rehearse it; do not skip crop confirmation or mislabel a fixture to meet the duration. This script satisfies the outline's "steps or recording" deliverable; a timed recording is a separate artifact.

## Error-state walkthrough

Use the same public sample. In field review choose `recapture_required`, `invalid_file`, `offline`, `timeout`, and `error`, running Check image quality after each change. Rejected/failed quality must never enable cell selection. Change to `inconclusive`, rerun quality, and proceed to crop selection.

After confirming a crop, use its Demo controls to select `offline`, `timeout`, or `error`. Submit, verify an error and retry affordance, then select `inconclusive` and retry the same crop. Select `review_required` and `analysis_complete` on subsequent submissions to review the other result copy. All simulated results must remain labeled. Replace crop must reopen the original field, and Retake field must return to capture. Mock invalid-file responses do not prove native gallery validation; the unit suite separately checks pre-upload rejection.

For actual network timeout testing, use a controlled slow real endpoint; the automated suite exercises a stalled response body. Camera permission, emulator shutter and gallery import received the scoped evidence below. Permission denial/permanent denial, gallery cancel, orientations and real-network checks still need further device evidence.

## Target-device record

| Field | Current evidence |
| --- | --- |
| Test target | Android Studio AVD `Medium_Phone` |
| Runtime | Android 15; `sdk_gphone64_x86_64`; Expo Go 57.0.9 |
| API mode | Explicit development mock for this walkthrough |
| Physical phone model / OS | Not supplied; owner requested emulator for now |
| Microscope/adapter | Not used |
| Real model / Huawei endpoint | Not exercised by this simulated walkthrough |
| Native release APK | Not built/installed in this pass |

See [the mobile tests checklist](../apps/mobile/tests/README.md) for physical-device acceptance. Emulator evidence does not close the target-phone items.

## Unchecked outline items and disposition

| Day | Unchecked item in the supplied outline | Current disposition |
| --- | --- | --- |
| 2 | Working capture and gallery import on the target Android phone | Partial: app implementation exists; emulator verification is recorded below. Physical target phone remains pending by owner choice. |
| 2 | Short recording or screenshots showing the flow | Complete for emulator/software scope: [screenshot evidence](evidence/mobile-2026-11-18/README.md). |
| 4 | Tested end-to-end phone flow: capture/import, quality, crop, upload, result | Partial: public-sample emulator flow with simulated API verified. Actual phone, real upload/inference and target network are not verified in this pass. |
| 4 | Retake, inconclusive, offline, timeout, invalid-file and server-error evidence | Complete for simulated emulator paths plus automated client checks; actual network/device failure injection remains pending. |
| 5 | Final Android build/run instructions and target-phone details | Partial: Windows run/build instructions and emulator identity provided above; physical phone details remain unavailable. |
| 5 | Final regression evidence for capture, crop, quality rejection, results, history and errors | Complete for the documented local/emulator scope; no claim of physical-device acceptance. |
| 5 | Repeatable three-minute demo steps or recording | Complete: timed script above. No live-endpoint recording was produced. |

## Regression results

- `npm run mobile:typecheck` - passed after the camera overlay correction.
- `npm run mobile:lint` - passed after the camera overlay correction.
- `npm run mobile:test` - 20 passed, 0 failed after the camera overlay correction.
- Metro bundled Android successfully for Expo Go; this is not a standalone APK build.
- Emulator walkthrough: research acknowledgment, dashboard navigation, public sample preview, simulated quality acceptance, crop dragging/resizing (286 x 246 to 308 x 268 pixels), actual crop preview and confirmation, offline/timeout/server error without lost crop, retry to simulated inconclusive, saved session/history, simulated quality rejection, invalid-file error, and retake navigation.
- The results screen displays simulation labeling and the research disclaimer. History displays the local session ID, timestamp, accepted quality, inconclusive state and `MOCK-NOT-A-MODEL`. Emulator clock displays its own timezone; screenshot times are not Manila timestamps.
- Demo controls were wired into Settings and review/crop screens. Field fixture changes clear stale quality acceptance; controls are hidden during review/submission requests. The camera overlay was moved outside `CameraView` after native testing exposed its unsupported child warning.
- Automated tests cover real-client multipart construction, response validation, network/server failures, stalled response-body timeout, image-file validation, crop geometry, history metadata and production mock exclusion. They do not render native UI or demonstrate live inference.

No model, dataset, backend contract, deployment or production credentials were changed for this mobile work. The original PDF has not been edited; this evidence-backed table is the completion record.

### Follow-up native emulator checks

Camera permission was granted. After moving the focus overlay to a sibling of `CameraView`, the native preview rendered without the unsupported-child warning. The shutter returned an image and navigated to review; its still was a dark emulator test frame with a timestamp, so this is capture-plumbing evidence, not image-fidelity validation. Retake returned to capture. The Android photo picker imported a local HemoScope startup screenshot and displayed it in review. No biological interpretation or simulated classification was performed on those non-cell test images. See screenshots 14-16 in the evidence index.
