# Model card template

Complete this record for each candidate checkpoint. Do not fill unknown fields with estimates or illustrative metrics.

## Identity

- Model name/version: [To be completed]
- Checkpoint SHA-256: [To be completed]
- Date and code revision: [To be completed]
- Preprocessing version/hash: [To be completed]
- Intended task: Selected-cell morphology research screening associated with B-ALL.

## Intended use and limits

- Intended users: [To be completed]
- Intended use: Educational and research demonstration for one manually selected cell.
- Out-of-scope: Patient diagnosis, disease exclusion, risk estimation, treatment, whole-smear classification, and clinical deployment.
- Human review requirement: [To be completed]

## Data provenance and split

- Dataset and version: [To be completed]
- Permission and attribution record: [To be completed]
- Image and subject counts by class: [To be completed]
- Subject-level split procedure, seed, and manifest hash: [To be completed]
- Phone-capture evaluation source and independent label process: [To be completed]
- Known dataset and domain limitations: [To be completed]

## Training and preprocessing

- Architecture and pretrained source: [To be completed]
- Training configuration and software versions: [To be completed]
- Image size, color conversion, normalization, and augmentation: [To be completed]
- Checkpoint selection criterion: [To be completed]
- Threshold and abstention interval selection from validation only: [To be completed]

## Evaluation

| Partition | Sample count | Sensitivity | Specificity | Weighted F1 | Confusion matrix |
| --- | --- | --- | --- | --- | --- |
| Validation | [To be completed] | [To be completed] | [To be completed] | [To be completed] | [To be completed] |
| Held-out test | [To be completed] | [To be completed] | [To be completed] | [To be completed] | [To be completed] |
| Phone crops | [To be completed] | [To be completed] | [To be completed] | [To be completed] | [To be completed] |

Report denominators, confidence intervals where feasible, abstention and rejection rates, and failure examples. Do not report a score as a calibrated probability unless calibration is measured and documented.

## Failure modes and maintenance

- Known failure cases: [To be completed]
- Equipment, stain, population, or image-quality gaps: [To be completed]
- Update and rollback process: [To be completed]
- Monitoring and reviewer feedback process: [To be completed]
- Clinical performance statement: Not established by this research scaffold.
