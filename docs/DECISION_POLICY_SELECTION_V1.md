# Provisional decision policy selection v1

Selected by the user on 15 November 2026 (Asia/Manila): **Option B**, the inconclusive interval from 0.30 inclusive to 0.70 exclusive. The API contract, mobile display, standalone inference bundle and optional local API adapter carry the selected fields and wording. Live Huawei inference remains pending. See [the implementation record](OPTION_B_IMPLEMENTATION_V1.md).

## Selected behavior

For a real model result from an accepted and manually confirmed single-cell crop:

- ALL-class score below 0.30: `analysis_complete` with the warning “No model flag at this research threshold. This does not rule out disease.” The warning also includes the research-use disclaimer.
- Score at least 0.30 and below 0.70: inconclusive and qualified review required.
- Score at least 0.70: morphology flag and qualified review required.

The score must be the explicit ALL-class score, not the winning class's score returned by the present wrapper. Quality rejection and model errors must still stop classification and cannot become low-score results. Low-score output does not rule out disease.

## Evidence binding

This provisional choice is based on the lower-rate model `hemoscope-mobilenetv3-small-grouped-lowlr-v1`, checkpoint SHA-256 `58b80cd5ce7478ba218a7f374715f849734a4665b2e7d219db2cf56752cf2b98`, frozen split SHA-256 `38a8b633f49592dae8f068942af6494d6d7a636723b7d3e439f16929cdad564a`. The original [proposal](DECISION_POLICY_PROPOSAL_V1.md) and local `ml/artifacts/policy-proposals/decision-v1/evidence.json` retain the validation counts and limitations.

On 1,486 validation images it defers 178 (101 ALL, 77 normal), classifies 1,308, puts 37 ALL images in the low-score region, and flags 103 normal images. The 89.13% weighted F1 applies only to the 1,308 classified images. It must not replace the full-cohort 85.83% argmax F1 as though the underlying classifier improved.

## Model refinement remains open

Selecting this output policy does not freeze the model as the final candidate. Continue measuring full-cohort classifier performance, ALL sensitivity, normal specificity, subject-level errors, score coverage and deferrals. Future training remains user-run; Codex may prepare controlled configurations and run authorized diagnostics/evaluations.

Compare future model changes on the same versioned development split with recorded settings. Avoid an unlimited search for the highest validation score; repeated selection can overfit validation. Reserve independently audited untouched data for final assessment after weights, preprocessing and policy choices are fixed. A stronger candidate must re-evaluate and version its own decision policy rather than automatically inheriting these thresholds.

No optimum accuracy, clinical reliability or phone-image generalization is established by this selection. The desired error/coverage trade-off still needs explicit documentation. The response state and ALL-score semantics are implemented for the local model path; live Huawei inference remains pending.

## Step boundary and checklist

Complete: policy-selection portion of Developer 1's Day 3 threshold/inconclusive task.

Completed: explicit ALL-score output, policy logic, exact-boundary/error checks and validation replay; API schema, OpenAPI/generated mobile types, result display and documented contract semantics; local adapter wiring to the packaged candidate. Pending: final candidate freeze, independently labeled phone-crop evaluation and cloud deployment. No model weights or training settings changed by the integration work.
