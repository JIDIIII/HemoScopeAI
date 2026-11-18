# Emulator mobile evidence - 18 November 2026

Captured from the running app using Android Debug Bridge, not design mockups. Target: `Medium_Phone`, Android 15, x86_64, Expo Go 57.0.9. API mode: explicit development simulation. Screenshots show the emulator's clock/timezone, not necessarily Asia/Manila time.

The cell image in screenshots 04-13 is the bundled CC0 public software-flow sample by Mikael Haggstrom; see [source, attribution and limitations](../../../samples/public/README.md). It is not C-NMC, a team microscope capture or evidence of classifier accuracy. The floating gear is Expo Go's development overlay.

| Screenshot | Observed behavior |
| --- | --- |
| [01 - Research notice](01-research-notice.png) | Research-use acknowledgment before entry. |
| [02 - Dashboard](02-dashboard.png) | Navy actions and pill navigation with separate capture button. |
| [03 - Capture entry](03-capture.png) | Permission affordance, gallery and bundled sample entry. |
| [04 - Quality accepted](04-quality-accepted.png) | Explicit demo controls and simulated accepted quality. Content below the viewport is scrollable. |
| [05 - Crop selection](05-crop-selection.png) | Original field, draggable selection and preview. |
| [06 - Crop preview](06-crop-preview.png) | Drag/resize changed selection from 286 x 246 to 308 x 268; actual cropped preview and confirmation. |
| [07 - Offline](07-offline-retry.png) | Simulated offline failure retains the confirmed crop and offers retry. |
| [08 - Timeout](08-timeout-retry.png) | Simulated timeout retains the crop; not a measured network timeout. |
| [09 - Server error](09-server-error.png) | Explicit failure, no negative finding, retry available. |
| [10 - Inconclusive](10-inconclusive-result.png) | Retry using the same crop reaches an explicitly simulated inconclusive result and research notice. |
| [11 - History](11-history.png) | Saved local ID, timestamp, quality, simulation state and mock model version. |
| [12 - Rejection](12-quality-rejection.png) | Simulated focus rejection with recapture guidance; no cell-selection action. |
| [13 - Invalid file](13-invalid-file.png) | Simulated invalid-file error; retake returns to capture. |
| [14 - Emulator camera](14-emulator-camera.png) | Native camera permission granted; virtual scene preview and corrected sibling overlay. |
| [15 - Camera image preview](15-camera-image-preview.png) | Shutter returns an image to review. The emulator-produced still is a dark test frame with a timestamp, not a faithful microscope/scene capture; image suitability and physical-camera correctness are not established. |
| [16 - Gallery import](16-gallery-import.png) | Native Android photo picker imports a local HemoScope startup screenshot into review. This verifies image import/preview plumbing only; it is not a biological image and was not submitted as model evidence. |

## Verification limits

No physical phone, microscope, real model or Huawei endpoint was used. Failure fixtures verify app response handling, not actual connectivity failures. Unit tests separately cover client timeout, invalid upload input and response validation. No native release APK was built in this pass. Permission denial/permanent denial, gallery cancel, all image orientations and every result state still require the broader native acceptance checklist.

The original screenshot bytes are retained; SHA-256 hashes are listed in `SHA256SUMS.txt`. No patient material or credentials were used. See [the handoff](../../DEVELOPER_2_MOBILE_HANDOFF_2026-11-18.md) for the seven-item checklist, run instructions and timed demo script.
