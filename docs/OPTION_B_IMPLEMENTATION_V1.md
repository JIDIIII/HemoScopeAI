# Option B ML implementation v1

Implemented 15 November 2026 (Asia/Manila). Scope: ML package only. API, mobile schemas, quality rules, weights and training settings are unchanged.

## Public outputs and rule

`CellClassifier.predict(image)` preserves the original argmax `model_label`, winning-class `raw_model_score`, model version and preprocessing metadata. It now also returns `all_score`, read from the class explicitly named `all`; it is independent of which class wins or its index in the checkpoint. Scores remain uncalibrated model outputs.

The separately versioned policy is `hemoscope-option-b-v1` in `ml/src/decision_policy.py`:

| ALL score | Policy status |
| --- | --- |
| Less than 0.30 | `analysis_complete`, with scoped low-score/research warning |
| At least 0.30 and less than 0.70 | `inconclusive`, qualified review required |
| At least 0.70 | `review_required`, qualified review required |

It binds to model version `hemoscope-mobilenetv3-small-grouped-lowlr-v1` and checkpoint SHA-256 `58b80cd5ce7478ba218a7f374715f849734a4665b2e7d219db2cf56752cf2b98`. A different version or checkpoint raises `PolicyBindingError`, even if the class names are the same. The fixed, immutable v1 policy is not a generic threshold override for future models.

## Calling the policy-enabled wrapper

```python
from pathlib import Path
from src.inference import CellClassifier

classifier = CellClassifier(
    Path("artifacts/baseline-grouped-lowlr-v1/best-checkpoint.pt"),
    device="cpu",  # or "mps" on the tested Mac
)
result = classifier.predict_with_policy(
    crop_image,
    quality_accepted=True,
    crop_confirmed=True,
)

result.prediction.all_score
result.prediction.model_label
result.prediction.raw_model_score
result.decision.analysis_status
result.decision.decision_policy_version
result.decision.message
```

The caller must actually run its quality checks and obtain crop confirmation before supplying these booleans. The ML method does not perform image-quality screening or establish biological crop suitability. If either flag is not exactly `True`, it raises `InferencePreconditionError` before calling the model. The backend remains responsible for returning its rejected-image or crop-confirmation response.

The policy is opt-in through `predict_with_policy`; existing raw `predict` behavior does not automatically change into a policy decision. A raw argmax class and a policy status describe different things. The mobile app must ultimately follow the backend status/message rather than threshold the winning-class score itself.

## Failure behavior

- Missing checkpoint: `ModelNotAvailableError`.
- Incompatible binary class/positive-class or preprocessing metadata: fails loading.
- Missing, non-floating, wrongly shaped or non-finite model logits: `InvalidModelOutputError`.
- Invalid ALL scores, including missing values, booleans, strings, NaN, infinity or values outside 0 through 1: `InvalidScoreError`.
- Wrong checkpoint/version: `PolicyBindingError` before image inference.

These exceptions never create `analysis_complete` or other successful policy outputs. API error mapping remains an integration task. No simulation is converted into real inference by this library method.

Scores are compared at their actual numeric precision, not rounded display precision. Exact Python values 0.30 and 0.70 belong to inconclusive and review-required respectively; values immediately below each boundary remain on the lower side. A displayed rounded value alone is not sufficient to infer the internal status.

## Verification evidence

Boundary/error tests cover both sides of the thresholds, invalid scores and logits, reversed class ordering, the distinction between ALL score and winning-class score, wrong model binding, preconditions stopping inference, and a missing checkpoint. These tests do not train a model.

The updated validation diagnostic confirms the checkpoint still reproduces 85.83% argmax validation F1 and no sampled wrapper label mismatch; the ALL score also agrees with batch evaluation within numerical precision. Its report is `ml/artifacts/diagnostics/option-b-implementation-v1/summary.json`.

Replay of all 1,486 existing validation scores through the new policy exactly matches the proposal:

| Actual label | Low-score output | Inconclusive | Review flag |
| --- | ---: | ---: | ---: |
| ALL | 37 | 101 | 771 |
| Normal | 397 | 77 | 103 |
| Total | 434 | 178 | 874 |

Replay results are saved at `ml/artifacts/policy-implementation/option-b-v1/replay.json`. A separate real-checkpoint wrapper check exercises representative states and near-boundary validation images, treating quality/crop flags as satisfied solely for that library integration check.

No original or grouped test-set images were scored. The weights are unchanged. These checks establish implementation consistency with the chosen rule, not clinical performance, calibrated uncertainty or target-phone suitability.

## Checklist and next boundary

Complete locally: explicit ALL-score output, selected policy implementation and boundary/error validation. The Developer 1 Day 3 threshold/inconclusive implementation portion is complete in the ML package.

Still pending: package and version the complete inference handoff, confirm low-score state and score semantics with Developers 2/3, map ML exceptions to API responses, and integrate the API/mobile workflow. This step does not complete cloud deployment or the whole Day 3 checklist. Model refinement remains open; a new checkpoint requires re-evaluation and a separately bound policy.
