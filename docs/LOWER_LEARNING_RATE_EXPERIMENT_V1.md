# Lower learning rate experiment v1

Prepared 15 November 2026 (Asia/Manila). Configuration prepared and checked; the user runs training locally as a separate action.

Compare `baseline-grouped-lowlr-v1` with the completed `baseline-grouped-v1` on exactly the same frozen grouping-v1 / grouped-v1 assignments. The single numerical training change is AdamW learning rate **0.0003 to 0.00003**. This applies to all trainable parameters, including the classifier; it is not a separate feature-extractor-only learning rate. The model version and output folder are distinct to preserve both experiments.

Keep pretrained MobileNetV3-Small, 224 by 224 RGB images, two frozen epochs, ten total epochs, batch size 32, seed 42, weight decay 0.0001, MPS and four workers. Preprocessing, augmentation, partition assignments, class-weight calculation and checkpoint selection by lowest validation loss are unchanged. MPS computations need not be bit-identical across runs.

## Question

Does reducing update size improve validation stability and the sensitivity/specificity trade-off? This is an experimental hypothesis, not a promised improvement. Use the full history and the best-loss checkpoint results; report all outcomes. The original grouped baseline has validation F1 84.30%, ALL sensitivity 95.05%, specificity 68.63% and loss 0.371783, selected at epoch 10.

## Run from the repository root

```sh
source .venv/bin/activate
cd ml
export SSL_CERT_FILE="$(python -c 'import certifi; print(certifi.where())')"
caffeinate -i python -u -m src.train --config configs/baseline-grouped-lowlr-v1.yaml
```

Expected output folder: `ml/artifacts/baseline-grouped-lowlr-v1/`. Expected image counts: training 7,678, validation 1,486, internal test 1,289. Training scores validation only. Do not run `--evaluate-only` for selecting this experiment. Keep the original grouped baseline intact.

After completion, review `history.jsonl`, `model-metadata.json` and the saved checkpoint. The user can reply "done" so Codex reads the saved files directly. The next decision follows that review; no threshold changes, further training runs or test predictions are authorized by this preparation step.

Preparation evidence: `ml/artifacts/preflight/baseline-grouped-lowlr-v1.json`. It confirms that only the learning rate and experiment identifiers differ, that pinned dataset/split checks pass, and that no model was created during the preflight.

Checklist: the local controlled-experiment setup is ready. The refinement run and comparison of validation results remain pending. This preparation does not complete another PDF day or the model's final validation/handoff.
