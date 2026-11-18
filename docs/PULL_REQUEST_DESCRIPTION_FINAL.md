# Polished mobile workflow and Android emulator evidence

## Summary

This PR improves the HemoScope Expo mobile experience and adds a reproducible software-validation record for Android. It introduces a polished tab navigation layout, respects the device reduced-motion setting, and refines capture, crop-review, and shared UI components.

It also documents the emulator-only walkthrough and updates the project's research, dataset, model-card, demo, and status records so completed work and unresolved approvals are clearly separated.

## What changed

### Mobile experience

- Added a custom bottom tab menu for Dashboard, History, and Settings.
- Moved the main screens into Expo Router's tab navigator.
- Added reduced-motion-aware navigation and UI behavior.
- Refined onboarding artwork, action buttons, capture, review, crop, and shared screen layouts.
- Preserved explicit simulation labeling and avoided simulated fallback behavior in production mode.

### Emulator validation

- Added a Windows and Android-emulator setup guide.
- Documented a repeatable mock-mode demo and simulated error-state walkthrough.
- Verified capture plumbing, Android gallery import, crop selection and confirmation, simulated quality checks, retry behavior, and local history in the emulator.
- Added an indexed set of 16 emulator screenshots with SHA-256 checksums.
- Updated the mobile test checklist and regression instructions.

### Research and provenance documentation

- Updated the C-NMC source review, dataset policy, candidate model card, demo checklist, and project status.
- Added a C-NMC provenance and institutional-oversight confirmation tracker.
- Recorded the limits of emulator evidence and the approvals that are still outstanding.

## Validation

- `npm run mobile:typecheck` — passed.
- `npm run mobile:lint` — passed.
- `npm run mobile:test` — 20 passed.
- Android 15 emulator validation on Expo Go 57.0.9 in explicit development mock mode.
- Camera permission, virtual-camera capture plumbing, Android photo-picker import, crop geometry and preview, simulated quality/rejection/error states, retry, and local history were exercised.

Supporting evidence:

- [Android emulator evidence index](evidence/mobile-2026-11-18/README.md)
- [Developer 2 mobile handoff](DEVELOPER_2_MOBILE_HANDOFF_2026-11-18.md)
- [Mobile tests checklist](../apps/mobile/tests/README.md)
- [SHA-256 screenshot checksums](evidence/mobile-2026-11-18/SHA256SUMS.txt)

## Known limitations

- No physical Android phone or microscope/adapter was validated.
- No native release APK was built or installed.
- The walkthrough used simulated API responses; live cloud inference and Huawei deployment were not exercised.
- C-NMC provenance and institutional oversight confirmations remain pending.
- Emulator evidence does not establish diagnostic accuracy, biological suitability, or clinical performance.
- Permission denial/permanent denial, gallery cancellation, all image orientations, and real-network failures require additional device validation.

## Scope and review notes

The deployment and authentication changes already merged into `main` are part of the base branch, not this PR's change set.

This PR adds no dataset images, model weights, credentials, patient data, or training outputs. The public sample used in the evidence is limited to software-flow demonstration and is not a leukemia-validation image.
