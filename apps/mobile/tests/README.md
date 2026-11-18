# Mobile regression evidence

Run `npm run mobile:test` from the repository root. Node's built-in runner uses TypeScript transpilation in isolated VM modules; no phone, images, network, backend, or model is required. These tests cover crop edge bounds and original-pixel mapping, upload input validation, quality/result schema failures, confirmed-crop multipart fields, network/timeout/server failures, and explicit mock contracts. They do not render React Native or prove gestures/camera/native module behavior.

Also run `npm run mobile:typecheck` and `npm run mobile:lint`. Android bundle export checks Metro, assets, and Hermes compilation, but does not produce an APK.

## Emulator follow-up

See the [Developer 2 handoff](../../../docs/DEVELOPER_2_MOBILE_HANDOFF_2026-11-18.md) and [16 emulator screenshots](../../../docs/evidence/mobile-2026-11-18/README.md) for the 2026-11-18 simulated workflow, error-path checks, camera/gallery limits, and passing 20-test regression. Physical-phone requirements below remain pending.

## Physical-phone acceptance record (pending)

Record phone model, Android version, build/Expo version, API mode and base URL (no secrets), model version, date, and elapsed request time. Every item below is pending until tested on a phone. `adb devices` listed no devices during this catch-up.

- [ ] Allow camera, deny camera, permanently deny camera, then recover through Settings. Gallery remains usable.
- [ ] Cancel gallery without navigation; reject unsupported HEIC/GIF, oversized and unreadable files.
- [ ] Capture and import portrait/landscape/EXIF-rotated images; verify preview orientation.
- [ ] Drag to all four edges and resize; parent scrolling must not move the crop during a gesture.
- [ ] Compare crop preview with the selected region in the original; confirm exactly one complete cell, including margins.
- [ ] Replace crop and verify original field is unchanged. Return to capture and verify camera resumes.
- [ ] Reject blurred, dark, overexposed and too-small fields/crops through the real quality API; no analyze request should follow rejection.
- [ ] Choose each development fixture in Settings. Confirm all fixture screens/history remain labeled simulated.
- [ ] For crop-only rejection testing, pass field review first, then change the mock scenario in Settings and return to the crop.
- [ ] Disable network or use a failing endpoint; preserve confirmed crop and retry without a crash or negative finding.
- [ ] Exercise a genuinely slow response/body download to verify the 15-second timeout; the mock timeout is an immediate failure fixture.
- [ ] Return malformed JSON, 422, 503 and server errors; no successful result should appear.
- [ ] Switch to real mode, restart Metro, and obtain a genuine model response with model version and scoped result copy.
- [ ] Reopen the app and saved history; verify timestamps, version and simulation labeling. Clear history and reopen.
- [ ] Simulate storage failure; a successful model response must remain visible with a save warning.
- [ ] Build/install native release, repeat the real flow, and attach an authorized screen recording.

A passing unit suite is not physical-device, hardware, cloud, or clinical validation.
