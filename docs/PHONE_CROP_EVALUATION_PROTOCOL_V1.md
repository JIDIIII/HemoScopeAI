# Phone-captured cell crop evaluation protocol v1

Status: preparation protocol only. No independent phone-crop evaluation has been performed.

## Purpose and scope

Evaluate how the frozen HemoScope AI selected-cell classifier behaves on manually selected, single-cell crops captured through the project's phone-to-microscope setup. This is a research/domain-shift evaluation. It does not establish diagnostic accuracy, clinical performance, or suitability for patient care.

Keep phone-capture results separate from C-NMC internal validation and test results. Describe a phone dataset from another acquisition setup as external testing only when it is genuinely independent of model development. For transparent reporting, follow the CLAIM 2024 distinction between internal testing on held-out development data and external testing on data from a separate source or setting: <https://doi.org/10.1148/ryai.240300>.

## Entry conditions

Do not start image collection until all are true:

- The slide/image source is authorized for this research activity and the appropriate institutional oversight determination has been recorded.
- A qualified laboratory partner has approved the capture and cell-label review procedure.
- Images are de-identified. The manifest contains opaque study IDs only, never patient names, medical record numbers, accession numbers, or source slide labels.
- A controlled, access-limited storage location and retention/deletion plan are in place. Raw images and the manifest stay out of Git and ordinary issue/chat attachments.
- The phone, microscope, eyepiece, adapter, illumination, and capture settings are recorded using the [hardware capture protocol](HARDWARE_CAPTURE_PROTOCOL.md).
- The evaluation cohort and split rule are set before looking at model outputs.

If authorization, oversight, or qualified reference labeling cannot be established, stop at a capture-feasibility exercise and do not report classification performance.

## Freeze the candidate before evaluation

Record these values in the run report before inference:

- Model/version and checkpoint SHA-256.
- Inference bundle/version and preprocessing configuration/hash.
- Quality-gate version and acceptance criteria.
- Decision-policy version and exact boundaries. For the current Option B candidate: ALL score below `0.30` is the scoped low-score state; `[0.30, 0.70)` is inconclusive; `0.70` or higher is review required. These are research workflow states, not a diagnosis or calibrated probability.
- Capture setup profile and collection date range.
- Code revision and the manifest/split hashes.

Use the local inference bundle for this research step; do not treat a mock API response as a model prediction. Do not change the checkpoint, preprocessing, quality gate, or policy after opening the locked phone-test cohort. If they must change, create a new version and evaluate it on a new untouched cohort.

## Capture and crop procedure

1. Follow [Hardware capture protocol](HARDWARE_CAPTURE_PROTOCOL.md). Record setup metadata once per `capture_session_id`; record deviations for individual captures.
2. Capture a complete microscope field first and assign an opaque `field_group_id`.
3. Manually select one cell and save the model-input crop as a separate image. Preserve a private linkage from the crop to its source field using `field_group_id`; do not add identifiers to filenames.
4. Confirm the crop contains the whole selected cell, without truncation, and has the dimensions/format accepted by the current inference path. Record width and height after cropping.
5. Apply the project's documented quality gate before classifier inference. Record accepted and rejected crops, along with each rejection reason. Do not remove rejected crops from the capture-usability denominator.
6. If multiple crops or repeated captures come from the same cell, field, slide, specimen, or capture session, assign stable opaque grouping IDs. Keep related material together in one partition.
7. Do not selectively recapture or omit difficult cells after seeing model scores. Document capture failures and any predeclared exclusion with a reason.

The classifier input is one confirmed cell crop, not a complete field and not a whole-slide image. Do not infer whole-slide or patient status from a selected cell.

## Reference labels

- Have an appropriately qualified reviewer assign a cell-level reference label of `all` or `hem` only when the reviewer can support that label under the approved study procedure.
- Keep reviewer decisions blind to model scores and policy states where practical. Record the number of reviewers and how disagreements were resolved.
- Use `indeterminate`, `ungradable`, or `discordant` as annotation statuses when a definite label is not supported. Do not force these cases into `all` or `hem` for the primary labeled analysis.
- A case-level, slide-level, or patient-level label does not automatically establish the label of every cropped cell. The reviewer must confirm the selected-cell label.
- Record label provenance and adjudication method in the run report without names or direct identifiers.

The CSV template uses `reference_label` only for the agreed `all`/`hem` labels and `annotation_status` for review state. Keep uncertain or unresolved cases in the manifest so their counts remain visible.

## Cohort separation and leakage controls

Before inference, assign each specimen/slide group to exactly one of:

- `phone_dev`: permitted for debugging capture and integration issues; not used to claim final performance.
- `phone_locked_test`: kept unopened for final evaluation after the system is frozen.
- `excluded`: excluded for a documented reason, such as missing authorization or unreadable/corrupt data.

Split at the highest available biological/source grouping level. All cells, fields, repeated captures, and crops from the same slide or specimen must remain in one partition. When slide/specimen relationships cannot be verified, treat the data as development-only and disclose the grouping uncertainty; do not call it an independent test.

Use opaque `specimen_group_id`, `slide_group_id`, `field_group_id`, and `cell_group_id`; do not store a re-identification key in the repository. Check exact duplicate file hashes and review likely near-duplicates before finalizing the split. A crop copied, resized, or re-encoded from another partition must not cross partitions.

For a claim of independent phone testing, also verify that the phone cohort does not reuse subjects/specimens or source images from the C-NMC training, development, or test partitions, or from any phone data already used to choose the model or policy. If source overlap cannot be checked, call the results exploratory phone-capture results rather than independent external testing.

Do not choose thresholds, quality criteria, preprocessing, or model settings based on `phone_locked_test`. If the available number of independent specimen/slide groups is too small to preserve a meaningful locked cohort, report the collection as exploratory/development data and defer final phone testing.

## Evaluation and reporting

Report the data flow and denominators separately:

1. **Capture usability:** number of attempted fields/crops; number passing the quality gate; and rejection counts by reason.
2. **Reference labeling:** counts for `all`, `hem`, `indeterminate`, `ungradable`, and `discordant`; reviewer count and adjudication method.
3. **Classifier on quality-accepted, definitely labeled crops:** sample count, class counts, confusion matrix, sensitivity, specificity, precision, and F1. State which class is positive (`all`), the frozen raw-score-to-label rule used, and show raw counts with every rate.
4. **Policy behavior:** counts and coverage for low-score, inconclusive, review-required, and quality-rejected outcomes. Report metrics for policy-resolved cases separately from overall coverage; never turn low score into a normal/negative patient result. Treat `all_score` as an uncalibrated model score unless calibration has separately been measured and documented.
5. **Grouping and uncertainty:** number of independent specimens/slides and relevant device/setup subgroups. Do not treat repeated crops or cells from one specimen as independent observations. If the number of independent groups supports it, calculate uncertainty intervals by resampling at the specimen/slide group level; otherwise state that reliable group-level intervals could not be estimated.
6. **Failure review:** include de-identified examples of focus, lighting, stain, crop-selection, and model errors only in approved private storage. Do not put raw source images into Git.

Report phone-test metrics only after the locked cohort has been evaluated once with the frozen candidate. Do not compare a phone score directly with C-NMC as though the cohorts were interchangeable. Include device/setup limitations and explicitly state that research evaluation is not clinical validation.

## Dataset manifest

Use the blank [phone-crop manifest template](PHONE_CROP_EVALUATION_MANIFEST_TEMPLATE.csv). Keep the populated copy and image files in the approved private data location. Its opaque IDs must be stable across the field image, crop, annotation, and split records, but must not encode personal information.

For the template, use `partition` values `phone_dev`, `phone_locked_test`, or `excluded`; `quality_status` values `accepted`, `rejected`, or `not_assessed`; `annotation_status` values `reviewed`, `indeterminate`, `ungradable`, or `discordant`; and `reference_label` values `all`, `hem`, or blank. Fill the label only for a definitely reviewed crop. Leave inference columns blank until that exact frozen model/policy has run. Store a relative path or opaque file key, not a path containing a person's name or other identifier. Keep detailed rejection reasons and notes free of identifying information.

## Developer 1 checklist status

- Protocol and blank manifest template: prepared.
- Physical phone/microscope capture and qualified cell-level labels: pending hardware access and authorized review.
- Independent locked phone-test evaluation: pending captured, labeled data and a frozen candidate.
- Model-card phone-crop results: pending evaluation; do not enter estimates.
