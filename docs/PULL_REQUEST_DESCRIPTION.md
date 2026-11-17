# Complete Developer 2 mobile research workflow and fix analysis integration

This PR connects the mobile research workflow from onboarding and image capture through field review, manual cell selection, confirmed-crop analysis, and local result history. It also fixes request mismatches that prevented live analysis and blocked valid small crops.

## Mobile changes

- Add research onboarding, dashboard navigation, shared branding, capture guidance, and settings with backend connection checks.
- Support camera capture and gallery import with input validation, permission handling, loading states, and error messages.
- Review the original field through `/quality`, then let the user drag and resize a cell selection, preview the generated JPEG, and explicitly confirm the crop.
- Submit only the confirmed crop to `/analyze` and display scoped results for completed analysis, qualified review, inconclusive results, and recapture requirements.
- Preserve the crop for retry after request failures and retain received results when local history cannot be saved.
- Add local metadata history with filtering, sorting, deletion, model details, and simulation labels. History does not persist image content.
- Provide opt-in development fixtures. Production uses the real API, and failed live requests never silently fall back to simulated results.
- Add mobile regression tests, a mobile CI test step, setup documentation, and a Developer 2 handoff record.

## Integration and runtime fixes

| Problem | Resulting behavior |
| --- | --- |
| `local-…` history IDs were sent to a UUID-only API field, causing HTTP 422. | Omit non-UUID values from the optional `research_session_id` field. Local history retains its existing IDs; valid UUIDs are still transmitted. |
| Selected crops were checked against `/quality` full-field dimension limits. | Send confirmed crops directly to `/analyze`, which applies crop-specific quality checks before inference. Keep `/quality` for the original field. |
| Browser uploads serialized native image descriptors as `[object Object]`. | Upload binary image data with safe filenames on web; preserve native URI uploads on Android. |
| History deletion used a native alert that does nothing on web. | Use browser confirmation on web and native confirmation on mobile for deleting or clearing history. |
| The recapture demo response reported accepted quality. | Mark it rejected and reject contradictory quality/analysis responses at runtime. |

## Validation

Verified on 16 November 2026:

- `npm run mobile:test` — all 16 tests passed.
- `npm run mobile:typecheck` — passed.
- `npm run mobile:lint` — passed.
- `git diff --check` — passed before commit.
- Headless Chrome at a mobile viewport — onboarding, gallery import, field review, crop preview/confirmation, binary uploads, results, automatic history save, delete cancellation/confirmation, clearing history, server failure, retry, and crop rejection passed without browser page errors.

Browser testing used a synthetic image and controlled API responses. It verifies UI and request handling, not live model inference. Regression coverage includes direct submission of a 128 × 128 crop without a full-field quality precheck; real crop acceptance remains the backend's responsibility.

## Backend scope and CI repair

Commit `6226a6f` included pre-existing deletions of `services/api/`, `packages/contracts/`, and the API export/type-generation and structure-verification scripts under `scripts/`. This caused CI to fail while installing `services/api[dev]`.

Those files are now restored from `origin/main`. The mobile changes do not require deleting or changing the backend implementation or API contract. The repair preserves the existing mobile and merged ML commits. GitHub must rerun CI after the repair is pushed.

## Pending integration evidence

- Physical Android camera permissions, gestures, image orientation, and microscope capture validation.
- Native APK build and installation.
- A real authenticated backend endpoint and genuine model response, including model version and latency.
- Representative-image quality calibration and model evaluation by the responsible owners.

The delivered workflow is for research and education. UI tests do not establish diagnostic accuracy or clinical suitability.
