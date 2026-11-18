# Developer 2 catch-up and handoff

Current status, 16 November 2026: the backend, contracts, and generation scripts mentioned as deleted in the historical notes below have been restored from `origin/main` to repair CI. Confirmed crops now go directly to `/analyze` for crop-specific quality checks, and local history IDs are omitted from the optional UUID upload field. See `PULL_REQUEST_DESCRIPTION.md` for the current PR summary.

Updated 15 November 2026 (Asia/Manila). Scope: the Developer 2 items in the supplied five-day sprint (outline 6), PR checklist (outline 3), mobile requirements (outline 4), and repository ownership (outline 5). The five-day checklist governs this catch-up; the older seven-day blueprint supplies product requirements.

## Checkpoint status

| Day | Mobile work delivered                                                                                                                                                                                     | Evidence still needed                                                                |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| 1   | Existing welcome/navigation preserved; asset paths repaired; permission/loading/cancel/invalid-file handling; explicit development mock and real API client                                               | Target-phone run and camera/gallery permission verification                          |
| 2   | Full-field preview; drag/resize selection; normalized bounds mapped to original pixels; separate JPEG crop; preview and explicit complete-cell confirmation; multipart crop upload                        | Phone gestures, rotated camera/gallery images, and screen recording                  |
| 3   | Field and crop quality gates; rejection guidance; inconclusive/review-required/complete/error handling; original field retained for crop replacement; network/timeout/server failures keep crop for retry | Real authenticated HTTPS endpoint and genuine Huawei model response from Developer 3 |
| 4   | Metadata history, original timestamp preservation, simulated labels, saved result details, storage failure notices                                                                                        | End-to-end physical-phone evidence and failure/latency log                           |
| 5   | Regression tests, CI mobile test step, run/build guide, three-minute demo script                                                                                                                          | Native APK build/install and live demo recording                                     |

These are implementation statuses, not claims that device/cloud checkpoints have passed. No phone was listed by `adb devices`. No installable APK or physical-device screen recording was produced. A bundle export is not an APK. The working tree already contained deleted backend/contracts/scripts and uncommitted onboarding work; backend deletions were preserved. Backend/contract CI cannot pass from this working tree until its owner resolves those missing files.

## Reviewable PR descriptions

Use the following as PR descriptions against the team's sprint items. No PRs have been published and no teammate has been assigned or messaged. The changes currently form one working-tree catch-up; split commits with reviewed hunks if the team requires three separate PRs. Avoid staging the unrelated backend deletions.

### Day 1 — Complete mobile foundation and explicit development fixtures

Connect the existing onboarding and capture entry point to validated camera/gallery selection. Add an opt-in, development-only mock for health, quality, and analysis with a visible simulation banner; production always uses the real endpoint. Fix onboarding artwork paths and permit static PNG requires in ESLint.

Setup: install with `npm ci`, copy the mobile `.env.example`, choose `EXPO_PUBLIC_API_MODE=mock` for fixture testing, and restart Metro. Select scenarios in Settings. Reviewer role: Developer 3 for API behavior. Contract: no generated schema changes. Automated checks are documented below; Android permission and gallery behavior still require a connected phone.

### Day 2 — Produce and confirm a manually selected cell crop

Replace the crop placeholder with a draggable, resizable selection confined to the displayed image. Convert normalized selection coordinates to original pixels, generate a separate JPEG with Expo ImageManipulator, and require preview plus complete-cell confirmation. Submit only `cell_crop`, `crop_confirmed=true`, and the local research session ID. Retrying or replacing the crop preserves the original field.

Setup: `npm ci` installs the new SDK-compatible image manipulator dependency. Reviewer roles: Developer 3 for multipart integration and Developer 1 for crop suitability. Geometry and payload tests pass; crop gestures, orientation, and complete-cell suitability need physical-phone review. A user confirmation is not automated cell detection.

### Day 3 — Gate inference on crop quality and handle all result states

Check field quality before cell selection and crop quality before analysis. Clear stale quality approval on retry. Reject malformed or contradictory API responses, show scoped result instructions and model metadata, retain the crop on network errors, and distinguish simulated output in both results and history. Local-storage failures do not discard an already received model result.

Reviewer roles: Developer 3 for live endpoint integration and Developer 1 for uncertainty wording. No API contract changes. Mock scenarios and request failure tests pass; actual Huawei inference, authentication, calibrated quality thresholds, and live phone verification remain external handoffs.

## Verification record

Automated checks: `npm run mobile:test`, `npm run mobile:typecheck`, `npm run mobile:lint`. See `apps/mobile/tests/README.md` for coverage and device acceptance steps. No clinical or model performance claims follow from these checks.

On 15 November 2026: all 11 regression tests passed; TypeScript and ESLint passed. Android production export completed with Hermes bytecode and 32 bundled assets in the ignored `dist/mobile` directory. Hermes initially could not write the sandbox temporary directory; exporting with TEMP/TMP pointed to `dist/metro-temp` succeeded. No Android device was attached. No native APK was generated, and no Java executable was available on PATH for the native build workflow.

## Three-minute demo

1. 0:00–0:30: show research disclaimer and the approved phone/microscope setup.
2. 0:30–1:00: capture/import a de-identified field and show full-field preview.
3. 1:00–1:30: demonstrate a poor field rejected with actionable focus/exposure guidance.
4. 1:30–2:10: use an acceptable field, drag/resize to one complete cell, preview and confirm, then submit to the real HTTPS service.
5. 2:10–2:40: show result status, model version, research limits, and local history. Developer 3 supplies Huawei evidence.
6. 2:40–3:00: state measured evidence and outstanding limitations. If using fixtures, explicitly present this as a simulated software demonstration.

## Required integration handoff

Developer 3 supplies the HTTPS base URL and running `/health`, `/quality`, and `/analyze` routes matching `src/types/api.generated.ts`. The mobile client can use Supabase email/password sign-in and sends a short-lived access token in the `Authorization` header; the API validates it before accepting image uploads when configured. Do not embed Huawei credentials or Supabase secret/service-role keys in Expo public variables. Public service access still requires a configured Supabase project, issued accounts, and authenticated end-to-end validation. Backend remains responsible for checking bytes, dimensions, format and quality even if mobile checks pass.

Developer 2 records phone model/Android version, Expo Go or native build version, image orientation, capture/import behavior, crop accuracy, response timing, model version, and outcome in the test checklist. Obtain approved de-identified images; do not commit captures or identifiers.

## UI design implementation

The supplied November 2026 UI references now inform the dashboard, navigation, onboarding, capture controls, quality checklist, four-corner crop selector, result details, history filters/deletion, and grouped settings. Original supplied branding is under `apps/mobile/assets/brand`; the wordmark is displayed at its ink bounds without modifying the source. The alternate artboard is retained but not used because it has no visible dark artwork on a white background.

Validation: 12 logic tests, TypeScript, ESLint, Android bundle export, and a browser smoke test through mocked quality review, dragging a crop handle, native-module web crop generation, confirmation, simulated analysis, saved results, and history. Browser flow reported no page errors. Screenshots in ignored `dist/ui-review` use a nonclinical illustration as test input. This is UI evidence, not phone/microscope or live cloud evidence. Web support was added for visual preview; Android device validation remains pending.
