# Safety, privacy, and limitations

## Medical scope

HemoScope AI is an educational and research demonstrator. It does not diagnose leukemia, rule out disease, estimate patient risk, stage disease, or recommend treatment. It screens morphology in one manually selected cell only. A cell or field without a flag does not rule out leukemia or represent the full smear.

A failed, missing, or inconclusive model result is never a negative result. Suspicious morphology requires qualified review. The application is not approved for clinical use and no clinical performance is established.

## Data protection

- Use only authorized, de-identified teaching or research material.
- Do not capture or submit names, slide labels, requisitions, or personal identifiers.
- Do not log raw image bytes or personal information.
- Keep cloud credentials on the backend only.
- Use private object storage, least-privilege IAM, and controlled retention.
- Document authorization, access, deletion, and backup cleanup before storing any cloud images.
- Local history contains non-identifying session metadata; it can be cleared from the device.

## Image-quality limitations

Blur, brightness, clipped pixels, and minimum dimensions are engineering heuristics. The scaffold's values are development defaults, not validated microscopy thresholds. Stain, magnification, sensor, microscope optics, phone processing, and slide preparation can change the scores. Quality acceptance does not establish that a cell is biologically suitable. Upload byte and decoded-pixel limits are service safety caps, not microscopy quality criteria.

## Model limitations

No model is trained or included. C-NMC 2019 is a proposed cell-level research source; a model trained on segmented dataset images must not receive arbitrary full microscope fields. Phone-capture generalization is unknown until independently labeled phone crops are evaluated. Raw model scores are not calibrated probabilities by default.

## Deployment controls still required

Before exposing an endpoint outside a trusted development network, implement and verify authentication, TLS, rate limiting, request timeout and size limits, private storage, retention/deletion, access review, logging controls, backup cleanup, and incident response. Review applicable institutional, ethics, privacy, and medical-device requirements with qualified advisors before any clinical pilot.
