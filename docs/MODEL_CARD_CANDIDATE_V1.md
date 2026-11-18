# Preliminary model card — grouped low-learning-rate candidate v1

**Status:** provisional research candidate; model refinement and independent evaluation remain open. Prepared 15 November 2026.

This card records the current candidate for team review. It does not establish clinical performance, diagnostic accuracy, or suitability for patient care. The matching inference bundle includes its own preliminary model card; this tracked copy makes the summary reviewable in the repository. Keep the reusable [model card template](MODEL_CARD_TEMPLATE.md) unchanged for future candidates.

## Model identity

| Field | Recorded value |
| --- | --- |
| Model version | `hemoscope-mobilenetv3-small-grouped-lowlr-v1` |
| Checkpoint SHA-256 | `58b80cd5ce7478ba218a7f374715f849734a4665b2e7d219db2cf56752cf2b98` |
| Architecture | Torchvision MobileNetV3-Small, pretrained weights enabled, binary head |
| Labels | `all` = ALL malignant B-lymphoblast cell; `hem` = normal B-lymphoid precursor cell, according to C-NMC source labels |
| Code revision at training time | Not recorded in the saved model metadata |
| Preprocessing | RGB; bilinear square resize to 224×224; tensor scaling to 0–1; mean `[0.485, 0.456, 0.406]`; standard deviation `[0.229, 0.224, 0.225]`; PIL bilinear interpolation |
| Runtime versions recorded | Python 3.13.12; PyTorch 2.15.0; Torchvision 0.29.2; training device MPS |

## Intended use and limits

The model accepts one manually selected and confirmed complete cell crop from authorized, de-identified research or teaching material, after a separate image-quality check. It is an educational and research demonstrator for cell-level morphology experiments.

It is not a whole-field detector or whole-smear classifier. It must not be used to diagnose or exclude leukemia, estimate patient risk, guide treatment, or replace qualified laboratory review. A model score is uncalibrated. A low-score policy state does not mean that a patient is disease-free.

Any real result requires a qualified reviewer and the project’s warning/status policy. The current ML policy implementation does not itself perform quality assessment or establish that a crop is biologically suitable.

## Data provenance and cohort construction

The source is C-NMC 2019 Version 1 from The Cancer Imaging Archive (TCIA): Mourya et al. (2019), [ALL Challenge dataset of ISBI 2019 (C-NMC 2019), Version 1](https://doi.org/10.7937/tcia.2019.dc64i46r). The project’s [dataset review](C_NMC_DATASET_REVIEW_V1.md) records the source labels, attribution requirements, local counts, and unresolved access/oversight confirmations. The source images and trained weights are not included in the repository.

The source training subset contained 10,661 labeled cells and 73 source IDs. The local curated manifest excluded all 208 images from 104 exact-byte duplicate groups and retained 10,453 images. A conservative grouping policy placed reviewed exact and near-image relationships into 56 dependency groups; these groups do not prove patient identity or complete independence.

The frozen seed-42 split is recorded in [GROUPED_SPLIT_V1.md](GROUPED_SPLIT_V1.md):

| Partition | Images | `all` | `hem` | Source IDs | Dependency groups |
| --- | ---: | ---: | ---: | ---: | ---: |
| Training | 7,678 | 5,286 | 2,392 | 50 | 38 |
| Validation | 1,486 | 909 | 577 | 10 | 9 |
| Internal test | 1,289 | 893 | 396 | 13 | 9 |

Split manifest SHA-256: `38a8b633f49592dae8f068942af6494d6d7a636723b7d3e439f16929cdad564a`.

Known data limitations include unresolved source-identity relationships, a bounded rather than exhaustive near-duplicate review, and a small number of independent groups—especially normal-class groups—in the internal test partition. The grouped internal test is a revised development holdout, not an untouched external cohort. Its results must not be described as independent final testing.

The C-NMC training images are segmented cell images and do not represent the project’s target phone-to-microscope capture pipeline. No independently labeled phone-crop cohort has been evaluated. Before public reporting or distribution, retain the TCIA dataset citation and attribution details in the [dataset review](C_NMC_DATASET_REVIEW_V1.md). The source review now records Aspera transfer completion on 2026-11-13 from an owner-supplied screenshot, with source/version verification limitations. Institutional ethics/oversight determination remains pending.

## Training and model selection

| Setting | Value |
| --- | --- |
| Training configuration | `ml/configs/baseline-grouped-lowlr-v1.yaml` |
| Optimizer | AdamW |
| Epochs | 10 |
| Checkpoint selection | Lowest validation loss; selected checkpoint was epoch 10 |
| Batch size | 32 |
| Learning rate | 0.00003 |
| Weight decay | 0.0001 |
| Frozen backbone | First 2 epochs |
| Seed | 42 |
| Training augmentation | Random horizontal flip (p=0.5) and random rotation up to 5 degrees |
| Validation/inference augmentation | None |

This candidate was one controlled learning-rate comparison. It is not evidence that this learning rate is optimal. The Option B thresholds were chosen after reviewing the same development validation cohort, so the policy metrics below are exploratory and subject to validation-set selection effects.

## Validation results

The candidate was evaluated on the 1,486-image grouped validation partition: 909 `all` and 577 `hem` images. Confusion matrix rows are reference labels (`all`, `hem`) and columns are predicted labels (`all`, `hem`).

| Measure | Result |
| --- | ---: |
| Weighted F1, raw argmax | 85.83% |
| `all` sensitivity | 92.08% (837/909) |
| `hem` specificity | 76.43% (441/577) |
| Confusion matrix | `[[837, 72], [136, 441]]` |
| Mean validation loss | 0.34545 |

These are source-data development results. They do not establish performance on a new institution, patient population, slide source, microscope, or phone capture setup.

## Decision policy and abstention

The candidate is bound to `hemoscope-option-b-v1`, checkpoint SHA-256 as listed above:

- ALL score below `0.30`: `analysis_complete` with a scoped low-score/research warning.
- ALL score from `0.30` inclusive to below `0.70`: `inconclusive`; qualified review is required.
- ALL score of `0.70` or higher: `review_required`.

On the same 1,486 validation images, policy outcomes were 434 low-score, 178 inconclusive (101 `all`, 77 `hem`), and 874 review-required. Among the 1,308 images outside the inconclusive interval, conditional weighted F1 was 89.13%. This is conditional performance after deferral; it must not replace the full-cohort 85.83% raw-argmax F1 or be presented as an improvement to the underlying classifier.

## Test results and missing evidence

- Grouped internal-test partition: 1,289 images; **not evaluated** for this candidate. No test metrics are available.
- Phone-captured crops: **not evaluated**; collection protocol and blank manifest are in [PHONE_CROP_EVALUATION_PROTOCOL_V1.md](PHONE_CROP_EVALUATION_PROTOCOL_V1.md).
- External testing, calibrated scores, subgroup fairness, prospective use, and clinical performance: **not established**.
- Huawei/cloud inference and complete physical-device-to-cloud workflow: **not verified**.
- Target-device latency and memory profile: **not recorded**.

Do not tune the candidate or policy on the grouped internal-test partition. Any later model or policy change must receive a new version, matching checkpoint/policy binding, and a fresh evaluation plan.

## Known risks and maintenance

Potential errors can result from source and device shift, focus/lighting/stain differences, crop selection, class overlap, uncertain subject metadata, and limited numbers of independent groups. The model does not find cells in a full microscope field, reject poor-quality images, or provide calibrated clinical probabilities by itself.

Review errors with qualified laboratory support. Keep raw images and manifests in approved private storage, outside Git. Reassess this card when the checkpoint, preprocessing, policy, data split, or intended capture hardware changes.
