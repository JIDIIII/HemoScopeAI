# Grouped learning-rate comparison — validation only

**Prepared:** 15 November 2026 (Asia/Manila)  
**Scope:** compare the saved `baseline-grouped-v1` and `baseline-grouped-lowlr-v1` validation records. No training was run for this report, and no internal-test predictions were generated.

## Comparability check

Both runs use the same frozen grouped split, seed, data, preprocessing, architecture, batch size, weight decay, frozen-backbone schedule, epoch count, MPS device, and validation-selection rule. The saved split-manifest SHA-256 matches for both: `38a8b633f49592dae8f068942af6494d6d7a636723b7d3e439f16929cdad564a`.

The intended single training-setting change is AdamW learning rate:

| Run | Learning rate | Model version | Checkpoint SHA-256 |
| --- | ---: | --- | --- |
| Grouped baseline | 0.0003 | `hemoscope-mobilenetv3-small-grouped-v1` | `e1ca23a0183e7cea56327fa73f9998d213cb7eacb06ba3d1509d8e6bb8409bf2` |
| Grouped lower-rate | 0.00003 | `hemoscope-mobilenetv3-small-grouped-lowlr-v1` | `58b80cd5ce7478ba218a7f374715f849734a4665b2e7d219db2cf56752cf2b98` |

Both selected epoch 10 by minimum validation loss. Each result uses the same 1,486 validation images: 909 `all` and 577 `hem`.

## Selected-checkpoint results

| Metric | Grouped baseline | Grouped lower-rate | Change (lower-rate minus baseline) |
| --- | ---: | ---: | ---: |
| Validation weighted F1 | 84.30% | 85.83% | +1.53 percentage points |
| `all` sensitivity | 95.05% (864/909) | 92.08% (837/909) | −2.97 points; 27 more `all` misses |
| `hem` specificity | 68.63% (396/577) | 76.43% (441/577) | +7.80 points; 45 fewer `hem` cells flagged as `all` |
| Mean validation loss | 0.371783 | 0.345448 | −0.026335 |
| Confusion matrix, rows actual `all`,`hem`; columns predicted `all`,`hem` | `[[864, 45], [181, 396]]` | `[[837, 72], [136, 441]]` | — |

The lower-rate run has a modestly better selected validation F1 and loss, and higher `hem` specificity. It also has lower `all` sensitivity, with more missed `all` cells at the selected argmax decision. This is a tradeoff, not a uniform improvement.

## Epoch-to-epoch validation behavior

Across the ten saved epochs, the grouped baseline's validation loss ranged from `0.3718` to `1.6572`, and weighted F1 ranged from `27.63%` to `84.30%`. The lower-rate run's validation loss ranged from `0.3454` to `0.5502`, and weighted F1 ranged from `70.02%` to `85.83%`. The lower-rate trace was less variable in these recorded validation metrics.

This describes one run per setting. It does not show that learning rate alone caused the difference: MPS computations and training runs can vary, and there are no repeated seeds or independent validation cohorts here. Selecting epoch 10 by validation loss and comparing two settings on this same validation set can also favor the reported result through repeated model selection.

## Decision and limits

- Keep the lower-rate checkpoint as a **candidate for further review**, not as a proven optimal model.
- The sensitivity/specificity tradeoff should be considered alongside the project’s intended use and the chosen abstention policy; do not select settings by F1 alone.
- Do not change decision thresholds based on this comparison. Option B is bound to the lower-rate checkpoint, and changing weights requires a separately reviewed policy binding.
- Neither run's grouped internal-test partition was evaluated. Do not use this comparison as final test evidence.
- No independent phone-crop, external-source, calibration, or clinical evaluation is available.

## Developer 1 checklist status

The controlled learning-rate experiment and validation-only comparison are recorded. Model refinement remains open; further training is run by the user. The internal test remains reserved for a later, separately authorized evaluation after model and policy choices are frozen.
