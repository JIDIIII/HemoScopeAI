# Inference handoff v1 — Developer 1 to Developer 3

Prepared 15 November 2026 (Asia/Manila). This is a provisional local source bundle for integration. It has not been sent, published, deployed or qualified on Huawei Linux. Model refinement remains open.

## Deliverables

- Local archive: `ml/artifacts/handoff/hemoscope-inference-handoff-v1.zip`.
- Matching SHA-256 sidecar: `hemoscope-inference-handoff-v1.zip.sha256`.
- Expanded bundle: `ml/artifacts/handoff/hemoscope-inference-handoff-v1/`.
- Archive verification record: `ml/artifacts/handoff/handoff-v1-verification.json`.

These files are covered by the existing ignored model-artifact directory; do not force-add the checkpoint or source datasets to Git. Transfer the artifact through the team's approved private channel. No source images, cloud credentials or identifiable patient records are included.

The archive contains the exact selected checkpoint, standalone `hemoscope_inference` source namespace, preprocessing JSON, fixed Option B policy and its version, model metadata, preliminary model card, validation summary, tested runtime pins, CPU verification command, crop-prediction example, integrity manifest and API integration guidance.

## Versions and binding

| Item | Value |
| --- | --- |
| Bundle | `hemoscope-inference-handoff-v1` |
| Source-package version | `0.1.0` |
| Model | `hemoscope-mobilenetv3-small-grouped-lowlr-v1` |
| Checkpoint SHA-256 | `58b80cd5ce7478ba218a7f374715f849734a4665b2e7d219db2cf56752cf2b98` |
| Decision policy | `hemoscope-option-b-v1` |
| Policy bounds | below 0.30: scoped low-score output; [0.30,0.70): inconclusive; 0.70 or higher: review required |

Policy and preprocessing JSON describe the bound implementation; they are not runtime overrides. A different checkpoint must not inherit this policy without separate review and versioning.

## Developer 3's starting instructions

1. Extract the archive into a dedicated directory and read its `README.md`, `MODEL_CARD.md` and `INTEGRATION.md`.
2. Create an isolated Python environment and install the included runtime requirements. Dependency installation may require internet; the pinned versions describe the tested Mac runtime. Confirm compatible wheels and behavior on the actual Huawei host.
3. From the extracted bundle directory, run:

   ```sh
   python verify_bundle.py --self-test
   ```

   This verifies file hashes, blocks network connections/download functions, and checks local CPU inference and policy boundaries. Dependencies must already be installed. The synthetic example establishes packaging behavior, not accuracy or image quality.

4. For an approved crop whose quality and manual confirmation have already been established, run the supplied example:

   ```sh
   python -m examples.predict_crop --image /absolute/path/cell.png --quality-accepted --crop-confirmed
   ```

5. Integrate the result through the API's inference-adapter boundary in a separate change. Keep actual file validation, orientation/canonicalization, crop confirmation and quality rejection before model inference. Let the package apply its final RGB resize/normalization; do not normalize twice.

The package works directly from its directory. An optional `pip install .` path is described in the archive; installation/build tooling was not exercised by the offline source-bundle test. The model artifact must be retained and passed explicitly when using an installed package.

## Verified locally

- Bundle loads the selected local checkpoint on CPU with network connections and weight-download functions blocked.
- Sixteen validation samples match the saved policy states; the maximum ALL-score difference from the earlier saved MPS batch was about 0.000040.
- Checksums and the CPU self-test pass again after extracting the ZIP into a fresh temporary directory outside the repository.
- No actual model training or test-set evaluation was performed for this handoff. Original model artifacts retain their recorded hashes.

The runtime source export changes only its import namespace, dependency-help text and formatting. The bundle manifest records original and exported source hashes. A separate namespace avoids depending on the training project's generic `src` package.

## API decisions still requiring coordination

- The policy uses an explicit ALL-class score. Existing `model_label` and `raw_model_score` remain raw argmax outputs. Developer 2 should render the returned status/message rather than derive a new status from that winning-class score.
- `all_score` and `decision_policy_version` are available inside the ML output but are not currently API response fields. Keep them internal or coordinate schema/OpenAPI/generated-type changes before returning new fields.
- Confirm the completed low-score `analysis_complete` state with the team; it exists in the schema but was absent from the earlier shortlist.
- Handle missing/wrong-version models, malformed outputs and precondition failures using the agreed rejection/error paths. None may become a normal/negative result. Keep simulated responses clearly marked and separate from real inference.

## Evidence limits and checklist

Raw validation F1 remains 85.83%, sensitivity 92.08%, specificity 76.43%, on 1,486 images. Option B defers 178 images; its 89.13% conditional F1 applies only to the 1,308 classified images. These are development results with known source-dependency/threshold-selection limitations. Target-phone crops, independent final performance, cloud behavior and end-to-end Android integration remain unverified.

Developer 1's Day 3 **candidate model/preprocessing packaging** work is complete locally, with a versioned policy, checkpoint hash, usage example and limitations. The real cloud endpoint, actual accepted-crop request path, API agreement and integration evidence remain pending with the team. This handoff does not complete the entire Day 3 checkpoint or final Day 5 model freeze.
