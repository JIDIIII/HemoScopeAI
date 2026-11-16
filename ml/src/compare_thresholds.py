"""Compare validation-only score cutoffs and illustrative abstention bands offline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


def metrics(actual, predicted):
    actual = np.asarray(actual, dtype=bool)
    predicted = np.asarray(predicted, dtype=bool)
    tp = int(np.sum(actual & predicted))
    fn = int(np.sum(actual & ~predicted))
    fp = int(np.sum(~actual & predicted))
    tn = int(np.sum(~actual & ~predicted))
    positive, negative = tp + fn, tn + fp
    n = positive + negative

    def divide(a, b):
        return a / b if b else None

    f1_all = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    f1_hem = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.0
    return {
        "images": n,
        "all_images": positive,
        "normal_images": negative,
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "sensitivity": divide(tp, positive),
        "specificity": divide(tn, negative),
        "weighted_f1": (positive * f1_all + negative * f1_hem) / n if n else None,
        "accuracy": divide(tp + tn, n),
    }


def cutoff_metrics(actual, scores, cutoff):
    return {"cutoff": float(cutoff), **metrics(actual, scores >= cutoff)}


def band_metrics(actual, scores, lower, upper):
    if not 0 <= lower < upper <= 1:
        raise ValueError("Invalid inconclusive interval.")
    # Inconclusive cases never become normal/negative predictions.
    abstain = (scores >= lower) & (scores < upper)
    accepted = ~abstain
    measured = metrics(actual[accepted], scores[accepted] >= upper)
    return {
        "lower_inclusive": float(lower),
        "upper_exclusive": float(upper),
        "submitted_images": len(scores),
        "accepted_images": int(accepted.sum()),
        "inconclusive_images": int(abstain.sum()),
        "coverage": float(accepted.mean()),
        "inconclusive_all": int(np.sum(abstain & actual)),
        "inconclusive_normal": int(np.sum(abstain & ~actual)),
        "accepted_metrics": measured,
        "all_images_in_low_score_region_over_all_submitted_all": measured["false_negative"]
        / int(actual.sum()),
        "normal_images_flagged_over_all_submitted_normal": measured["false_positive"]
        / int((~actual).sum()),
    }


def read_predictions(folder):
    report = json.loads((folder / "summary.json").read_text())
    if report["partition"] != "validation" or report["test_images_evaluated"] != 0:
        raise ValueError("Only validation diagnostic inputs are accepted.")
    if not report["validation_reproduced_within_0_001"]:
        raise ValueError("Saved checkpoint validation was not reproduced.")
    with (folder / "predictions.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    if (
        len(rows) != len({r["image_path"] for r in rows})
        or len(rows) != report["metrics"]["sample_count"]
    ):
        raise ValueError("Prediction rows are duplicated or counts disagree.")
    rows.sort(key=lambda r: r["image_path"])
    for row in rows:
        score = float(row["all_score"])
        if (
            row["actual_label"] not in {"all", "hem"}
            or not math.isfinite(score)
            or not 0 <= score <= 1
        ):
            raise ValueError("Invalid class label or ALL score.")
        if row["predicted_label"] != ("all" if score >= 0.5 else "hem"):
            raise ValueError("Default prediction does not match ALL-score semantics.")
    actual = np.array([r["actual_label"] == "all" for r in rows])
    scores = np.array([float(r["all_score"]) for r in rows])
    if set(actual.tolist()) != {False, True}:
        raise ValueError("Validation inputs must include both source classes.")
    if (
        abs(metrics(actual, scores >= 0.5)["weighted_f1"] - report["metrics"]["weighted_f1"])
        > 1e-10
    ):
        raise ValueError("CSV metrics disagree with diagnostic summary.")
    return report, rows, actual, scores


def write_csv(path, rows):
    with path.open("x", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def compare(baseline: Path, lower_lr: Path, output: Path):
    if output.exists():
        raise FileExistsError("Use a fresh report directory.")
    directories = {"grouped_baseline": baseline, "lower_learning_rate": lower_lr}
    loaded = {name: read_predictions(folder) for name, folder in directories.items()}
    first, second = loaded.values()

    def keys(value):
        return [(r["image_path"], r["subject_id"], r["actual_label"]) for r in value[1]]

    if first[0]["split_sha256"] != second[0]["split_sha256"] or keys(first) != keys(second):
        raise ValueError("Both models must use identical validation images, IDs and labels.")
    target_sensitivity = first[0]["metrics"]["sensitivity"]
    results, sweeps, policies, subject_rows, bands = {}, [], [], [], []
    inputs = {}
    for name, (diagnostic, rows, actual, scores) in loaded.items():
        candidates = np.unique(np.concatenate(([0.0, 0.5, 1.0], scores)))
        sweep = [cutoff_metrics(actual, scores, threshold) for threshold in candidates]
        best_f1 = max(
            sweep,
            key=lambda r: (
                r["weighted_f1"],
                r["sensitivity"],
                r["specificity"],
                -abs(r["cutoff"] - 0.5),
            ),
        )
        matching = max(
            [r for r in sweep if r["sensitivity"] >= target_sensitivity],
            key=lambda r: (r["specificity"], r["weighted_f1"], -abs(r["cutoff"] - 0.5)),
        )
        selected = {
            "default_0_5": cutoff_metrics(actual, scores, 0.5),
            "maximum_validation_weighted_f1": best_f1,
            "match_baseline_default_sensitivity": matching,
        }
        results[name] = {
            "checkpoint_sha256": diagnostic["checkpoint_sha256"],
            "roc_auc": float(roc_auc_score(actual, scores)),
            "all_average_precision": float(average_precision_score(actual, scores)),
            "candidate_cutoffs": len(candidates),
            "selected_comparisons": selected,
        }
        sweeps.extend({"model": name, **r} for r in sweep)
        policies.extend({"model": name, "comparison": label, **r} for label, r in selected.items())
        for label, rule in selected.items():
            for subject in sorted({r["subject_id"] for r in rows}):
                mask = np.array([r["subject_id"] == subject for r in rows])
                subject_rows.append(
                    {
                        "model": name,
                        "comparison": label,
                        "subject_id": subject,
                        "cutoff": rule["cutoff"],
                        **metrics(actual[mask], scores[mask] >= rule["cutoff"]),
                    }
                )
        # Fixed illustrative bands, not an optimization over accepted-only accuracy.
        model_bands = [
            band_metrics(actual, scores, lower, upper)
            for lower, upper in [(0.4, 0.6), (0.3, 0.7), (0.2, 0.8), (0.1, 0.9)]
        ]
        results[name]["illustrative_bands"] = model_bands
        for rule in model_bands:
            bands.append(
                {
                    "model": name,
                    **{k: v for k, v in rule.items() if k != "accepted_metrics"},
                    **{"accepted_" + k: v for k, v in rule["accepted_metrics"].items()},
                }
            )
        inputs[name] = {
            "directory": str(directories[name]),
            "predictions_sha256": hashlib.sha256(
                (directories[name] / "predictions.csv").read_bytes()
            ).hexdigest(),
            "summary_sha256": hashlib.sha256(
                (directories[name] / "summary.json").read_bytes()
            ).hexdigest(),
        }
    output.mkdir(parents=True)
    write_csv(output / "cutoff-sweep.csv", sweeps)
    write_csv(output / "cutoff-comparisons.csv", policies)
    write_csv(output / "subject-comparisons.csv", subject_rows)
    write_csv(output / "inconclusive-bands.csv", bands)
    report = {
        "partition": "validation",
        "validation_images": len(first[1]),
        "validation_subjects": len({r["subject_id"] for r in first[1]}),
        "split_sha256": first[0]["split_sha256"],
        "test_images_evaluated": 0,
        "reference_sensitivity": target_sensitivity,
        "reference_note": (
            "Observed baseline default sensitivity, an exploratory comparison anchor; "
            "not a clinical requirement."
        ),
        "rules": {
            "binary": "ALL score >= cutoff flags ALL; otherwise normal-class output.",
            "inconclusive": (
                "score < lower: low-score output; lower <= score < upper: inconclusive; "
                "score >= upper: review flag."
            ),
            "selection": (
                "Binary cutoffs include every unique validation score and 0, 0.5, 1. "
                "Max F1 ties: sensitivity, specificity, closeness to 0.5. "
                "Sensitivity-matching ties: specificity, F1, closeness to 0.5."
            ),
        },
        "results": results,
        "inputs": inputs,
        "active_policy_changed": False,
        "limitations": [
            "Post-hoc tuning on the same small validation cohort produces optimistic estimates.",
            (
                "A threshold comparison is not independent evaluation "
                "or calibrated clinical probability."
            ),
            (
                "Conditional accepted-image metrics exclude abstentions; "
                "coverage and abstentions by true class are reported separately."
            ),
            (
                "No minimum coverage or acceptable error trade-off has been agreed; "
                "no inconclusive band is selected for deployment."
            ),
        ],
    }
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(output), "results": results}, indent=2))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline", type=Path, default=Path("artifacts/diagnostics/grouped-v1-mps")
    )
    parser.add_argument(
        "--lower-lr", type=Path, default=Path("artifacts/diagnostics/grouped-lowlr-v1-mps")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("artifacts/diagnostics/threshold-comparison-v1")
    )
    args = parser.parse_args()
    compare(args.baseline, args.lower_lr, args.output)


if __name__ == "__main__":
    main()
