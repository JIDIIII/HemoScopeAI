# Decision policy proposal v1

Prepared 15 November 2026 (Asia/Manila). **Option B was subsequently selected as the provisional research-demo policy; it is not yet active.** See [the selection record](DECISION_POLICY_SELECTION_V1.md). This document retains the alternatives and their original validation evidence. No model training or runtime configuration changes are part of this proposal.

## What the rule does

The model gives each selected cell an ALL-class score between 0 and 1. A decision policy translates that score into an app state and a message. These are research image-level outputs. A score of 0.35 does not mean a 35% probability that a person has leukemia, and a low score cannot rule out disease.

Both options below use the same lower-learning-rate checkpoint: `hemoscope-mobilenetv3-small-grouped-lowlr-v1`, SHA-256 `58b80cd5ce7478ba218a7f374715f849734a4665b2e7d219db2cf56752cf2b98`. The validation evidence covers 1,486 images (909 ALL and 577 normal), 10 source subjects and 9 dependency groups. It is post-hoc evidence from the development cohort, not independent or clinical validation. Neither the original nor grouped internal test has been newly scored for this proposal.

## Option A: one cutoff at 0.35

| ALL-class score | Proposed app state | Message |
| --- | --- | --- |
| Below 0.35 | `analysis_complete` | No model flag for this selected cell at the research threshold. This does not rule out disease. |
| 0.35 or higher | `review_required` | Morphology flag in the selected cell. Qualified review required. |

On the recorded validation set, this yields 864/909 ALL images flagged, 45 ALL images below the cutoff, 167/577 normal images flagged, and 410 normal images below the cutoff. Sensitivity is 95.05%, specificity 71.06%, and weighted F1 85.34%. No images are deferred by score. This matches the original grouped model's default aggregate sensitivity while flagging 14 fewer normal images; individual subject results still vary.

Trade-off: every quality-accepted image gets a binary score decision, including borderline cases. This option supplies no score-based inconclusive state. It is a useful comparison candidate but does not fulfill uncertainty handling by itself.

## Option B: a 0.30 through below-0.70 inconclusive range

| ALL-class score | Proposed app state | Message |
| --- | --- | --- |
| Below 0.30 | `analysis_complete` | No model flag for this selected cell at the research threshold. This does not rule out disease. |
| 0.30 or higher, below 0.70 | `inconclusive` | The model cannot provide a clear result for this selected cell. Qualified review is required. |
| 0.70 or higher | `review_required` | Morphology flag in the selected cell. Qualified review required. |

These bounds are a separately evaluated illustrative policy. **Do not combine them with Option A's 0.35 cutoff.** At exactly 0.30 the result is inconclusive; at exactly 0.70 it is a review flag.

| Actual validation label | Low-score output | Inconclusive | Review flag | Total |
| --- | ---: | ---: | ---: | ---: |
| ALL | 37 | 101 | 771 | 909 |
| Normal | 397 | 77 | 103 | 577 |
| Total | 434 | 178 | 874 | 1,486 |

This policy makes a score decision on 1,308/1,486 images (88.02% coverage) and defers 178 (11.98%). Among the 1,308 classified images, weighted F1 is 89.13%, sensitivity is 771/808 = 95.42%, and specificity is 397/500 = 79.40%. These conditional metrics exclude the inconclusive images and must not be presented as whole-cohort performance. Across all 909 ALL images, 771 are flagged, 101 are deferred, and 37 receive low-score outputs. A deferred ALL image is not counted as correctly flagged or silently counted as normal.

Trade-off: this exposes uncertainty in the demo and reduces the number of automatic score decisions. It still leaves 140 wrong classifications among accepted images (37 ALL low-score outputs plus 103 normal flags). Deferral is not a guarantee of correctness or a validated protection against confident errors. The observed 12% deferral rate is not an agreed maximum or a guarantee for phone images.

## Rules shared by both options

1. Apply file validation, image quality checks and explicit single-cell crop confirmation first. Failure of image quality produces `analysis_status: recapture_required` and `quality_status: rejected`; no model classification follows.
2. Apply score rules only to a quality-accepted, manually confirmed single-cell crop with a real, bound model version and valid output.
3. A missing/unavailable model, malformed score, non-finite score or processing error produces the structured error path. It never produces a low-score/normal result. The exact invalid-model-output error code must be agreed with Developer 3.
4. The development mock remains `inference_mode: simulated`, `analysis_status: inconclusive`, with no class or score. Simulation does not demonstrate that the selected threshold works.
5. Every real result displays the research-use limitation and applies the state returned by the backend. The mobile app must not independently threshold a score or convert model failures into negative results.
6. Inconclusive means a result was deferred; it is distinct from a rejected image and a completed low-score output.

## Important score and API detail

The present ML wrapper returns `model_label` from argmax and `raw_model_score` for that winning class. That score is not always the ALL-class score. If argmax is `hem` with score 0.60, the ALL-class score is approximately 0.40; Option A would flag it even though the raw argmax class is `hem`. Comparing the winning-class score to 0.35 would be incorrect.

Before implementation, expose the ALL-class score explicitly inside the inference package and apply the policy server-side. The team must document how this relates to the existing API fields. If the existing fields remain raw argmax outputs, keep their meaning and make the app follow `analysis_status` and the explanatory message. Adding or changing returned fields requires coordinated schemas, generated mobile types and documentation; this proposal makes no such change.

The existing API supports `analysis_complete`, but the team's recent shortlist named `review_required`, `inconclusive` and quality `rejected`. Confirm the completed low-score state before integration. `model_version` identifies the weights package; a separately versioned decision-policy identifier must identify the score rule, because changing thresholds changes behavior without changing weights.

## Decisions still needed

- Select one provisional research-demo option, or specify another explicit objective. Option B is the option here that supplies score-based uncertainty; that alone does not make it safer or clinically suitable.
- Agree whether the observed deferral workload and error trade-off are acceptable for the research demonstration. No acceptable clinical error rates or minimum coverage have been established.
- Confirm the low-score status/message and the ALL-score semantics with Developers 2 and 3.

After selection, implement and test the chosen boundary behavior, malformed-output handling and API mapping in a separately authorized step. Freeze the policy and bind its version to the exact checkpoint, preprocessing and grouping protocol before any reserved final assessment. Do not adjust the policy based on final test results. Real phone-crop evaluation and qualified review remain necessary for claims beyond the source-data experiment.

## Evidence and checklist

The measured figures and source hashes are saved locally in `ml/artifacts/policy-proposals/decision-v1/evidence.json`, derived from the existing validation predictions and the threshold comparison report. No new model inference or training was required.

Completed local step: prepare the decision-policy proposal with messages, trade-offs and open decisions. The Developer 1 PDF Day 3 threshold/inconclusive item remains **partial**: selection, implementation and packaging are still pending. This draft does not complete API agreement, cloud integration, final evaluation or model handoff.
