"""Create figures from saved validation-only diagnostics; never evaluates the test split."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)

from src.decision_policy import OPTION_B_V1

COLORS = {"grouped_baseline": "#3b82b8", "lower_learning_rate": "#e58b35"}
MODEL_NAMES = {
    "grouped_baseline": "Grouped baseline (LR 0.0003)",
    "lower_learning_rate": "Lower learning rate (0.00003)",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_run(name: str, diagnostics_dir: Path, run_dir: Path) -> dict:
    summary_path = diagnostics_dir / "summary.json"
    predictions_path = diagnostics_dir / "predictions.csv"
    history_path = run_dir / "history.jsonl"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if (
        summary.get("partition") != "validation"
        or summary.get("test_images_evaluated") != 0
        or summary.get("validation_reproduced_within_0_001") is not True
    ):
        raise ValueError(f"{name} is not a verified validation-only diagnostic.")

    with predictions_path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != summary["metrics"]["sample_count"]:
        raise ValueError(f"{name} prediction count differs from its saved summary.")
    if len({row["image_path"] for row in rows}) != len(rows):
        raise ValueError(f"{name} contains duplicate validation image paths.")

    truth, scores = [], []
    for row in rows:
        if row["actual_label"] not in {"all", "hem"}:
            raise ValueError(f"{name} contains an unknown label.")
        score = float(row["all_score"])
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError(f"{name} contains an invalid ALL score.")
        expected = "all" if score >= 0.5 else "hem"
        if row["predicted_label"] != expected:
            raise ValueError(f"{name} saved class label disagrees with its ALL score.")
        truth.append(row["actual_label"] == "all")
        scores.append(score)

    history = [
        json.loads(line)
        for line in history_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    best = min(history, key=lambda item: item["validation_metrics"]["mean_loss"])
    if best["epoch"] != summary["expected_best_epoch"]:
        raise ValueError(f"{name} history does not support the recorded best epoch.")
    if abs(best["validation_metrics"]["weighted_f1"] - summary["metrics"]["weighted_f1"]) > 1e-10:
        raise ValueError(f"{name} best history metrics disagree with diagnostic metrics.")

    truth_array = np.asarray(truth, dtype=bool)
    score_array = np.asarray(scores, dtype=float)
    predicted = score_array >= 0.5
    matrix = confusion_matrix(truth_array, predicted, labels=[True, False])
    tp, fn, fp, tn = (int(value) for value in matrix.ravel())
    all_count, hem_count = int(truth_array.sum()), int((~truth_array).sum())
    f1_all = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
    f1_hem = 2 * tn / (2 * tn + fp + fn) if 2 * tn + fp + fn else 0.0
    metrics = {
        "sample_count": len(rows),
        "all_count": all_count,
        "hem_count": hem_count,
        "true_positive": tp,
        "false_negative": fn,
        "false_positive": fp,
        "true_negative": tn,
        "sensitivity": tp / all_count if all_count else None,
        "specificity": tn / hem_count if hem_count else None,
        "weighted_f1": (all_count * f1_all + hem_count * f1_hem) / len(rows),
        "roc_auc": float(roc_auc_score(truth_array, score_array)),
        "all_average_precision": float(average_precision_score(truth_array, score_array)),
    }
    return {
        "name": name,
        "summary": summary,
        "summary_path": summary_path,
        "predictions_path": predictions_path,
        "history_path": history_path,
        "history": history,
        "best_epoch": best["epoch"],
        "rows": rows,
        "truth": truth_array,
        "scores": score_array,
        "metrics": metrics,
        "confusion_matrix": matrix,
    }


def load_validation_groups(manifest_path: Path, expected_sha: str, path_labels: dict) -> dict:
    if sha256(manifest_path) != expected_sha:
        raise ValueError("The frozen split manifest hash does not match the diagnostic records.")
    groups = {}
    with manifest_path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["split"] != "validation":
                continue
            image_path = row["image_path"]
            groups[image_path] = {
                "dependency_group": row["dependency_group"],
                "subject_id": row["subject_id"],
                "label": row["label"],
            }
    if set(groups) != set(path_labels):
        raise ValueError("Validation predictions do not match the frozen validation manifest.")
    for image_path, details in groups.items():
        if details["label"] != path_labels[image_path]:
            raise ValueError("A prediction label differs from the frozen validation manifest.")
    labels_per_group = defaultdict(set)
    for details in groups.values():
        labels_per_group[details["dependency_group"]].add(details["label"])
    if any(len(labels) != 1 for labels in labels_per_group.values()):
        raise ValueError("A validation dependency group contains mixed source labels.")
    return groups


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_epoch_curves(runs: dict, output: Path) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), constrained_layout=True)
    for name, run in runs.items():
        epochs = [row["epoch"] for row in run["history"]]
        loss = [row["validation_metrics"]["mean_loss"] for row in run["history"]]
        f1 = [row["validation_metrics"]["weighted_f1"] for row in run["history"]]
        color = COLORS[name]
        axes[0].plot(epochs, loss, marker="o", linewidth=2, color=color, label=MODEL_NAMES[name])
        axes[0].scatter(
            [run["best_epoch"]],
            [min(loss)],
            marker="*",
            s=150,
            color=color,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
        axes[1].plot(epochs, f1, marker="o", linewidth=2, color=color, label=MODEL_NAMES[name])
        axes[1].scatter(
            [run["best_epoch"]],
            [f1[run["best_epoch"] - 1]],
            marker="*",
            s=150,
            color=color,
            edgecolor="white",
            linewidth=0.7,
            zorder=3,
        )
    axes[0].set(title="Validation loss", xlabel="Epoch", ylabel="Weighted cross-entropy loss")
    axes[1].set(title="Validation weighted F1", xlabel="Epoch", ylabel="Weighted F1", ylim=(0, 1))
    for axis in axes:
        axis.set_xticks(range(1, 11))
        axis.grid(alpha=0.22)
        axis.legend(frameon=False, fontsize=8)
    fig.suptitle("Validation progress by epoch (stars mark the saved checkpoint)", fontsize=13)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    return fig


def plot_roc_pr(runs: dict, output: Path) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3), constrained_layout=True)
    prevalence = float(next(iter(runs.values()))["truth"].mean())
    for name, run in runs.items():
        color = COLORS[name]
        fpr, tpr, _ = roc_curve(run["truth"], run["scores"])
        precision, recall, _ = precision_recall_curve(run["truth"], run["scores"])
        axes[0].plot(
            fpr,
            tpr,
            linewidth=2,
            color=color,
            label=f"{MODEL_NAMES[name]} (AUC {run['metrics']['roc_auc']:.3f})",
        )
        axes[1].plot(
            recall,
            precision,
            linewidth=2,
            color=color,
            label=f"{MODEL_NAMES[name]} (AP {run['metrics']['all_average_precision']:.3f})",
        )
    axes[0].plot([0, 1], [0, 1], linestyle="--", color="#888888", linewidth=1, label="Chance")
    axes[1].axhline(
        prevalence,
        linestyle="--",
        color="#888888",
        linewidth=1,
        label=f"ALL prevalence ({prevalence:.3f})",
    )
    axes[0].set(
        title="ROC curve",
        xlabel="False positive rate",
        ylabel="True positive rate",
        xlim=(0, 1),
        ylim=(0, 1),
    )
    axes[1].set(
        title="Precision–recall curve",
        xlabel="Recall",
        ylabel="Precision",
        xlim=(0, 1),
        ylim=(0, 1),
    )
    for axis in axes:
        axis.grid(alpha=0.22)
        axis.legend(frameon=False, fontsize=8, loc="lower right")
    fig.suptitle("Validation ranking performance; one shared cohort", fontsize=13)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    return fig


def plot_confusion_matrices(runs: dict, output: Path) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(9, 4.3), constrained_layout=True)
    max_count = max(int(run["confusion_matrix"].max()) for run in runs.values())
    for axis, (name, run) in zip(axes, runs.items(), strict=True):
        matrix = run["confusion_matrix"]
        axis.imshow(matrix, cmap="Blues", vmin=0, vmax=max_count)
        axis.set_xticks([0, 1], labels=["ALL", "HEM"])
        axis.set_yticks([0, 1], labels=["ALL", "HEM"])
        axis.set_xlabel("Predicted label (score cutoff 0.50)")
        axis.set_ylabel("Dataset label")
        axis.set_title(f"{MODEL_NAMES[name]}\nF1 {run['metrics']['weighted_f1']:.1%}")
        for i in range(2):
            row_total = int(matrix[i].sum())
            for j in range(2):
                count = int(matrix[i, j])
                pct = 100 * count / row_total if row_total else 0
                color = "white" if count > max_count * 0.55 else "#17212b"
                axis.text(
                    j,
                    i,
                    f"{count}\n{pct:.1f}% of row",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=10,
                )
    fig.suptitle("Validation confusion matrices (counts and row percentages)", fontsize=13)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    return fig


def plot_score_distributions(runs: dict, output: Path) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3), constrained_layout=True, sharey=True)
    bins = np.linspace(0, 1, 31)
    class_styles = [
        (True, "ALL-labeled", "#4477aa"),
        (False, "HEM-labeled", "#cc6677"),
    ]
    for axis, (name, run) in zip(axes, runs.items(), strict=True):
        axis.axvspan(
            OPTION_B_V1.lower,
            OPTION_B_V1.upper,
            color="#f2cf66",
            alpha=0.18,
            label="Option B inconclusive band",
        )
        axis.axvline(OPTION_B_V1.lower, color="#8d7420", linestyle="--", linewidth=1)
        axis.axvline(OPTION_B_V1.upper, color="#8d7420", linestyle="--", linewidth=1)
        for is_all, label, color in class_styles:
            values = run["scores"][run["truth"] == is_all]
            axis.hist(
                values,
                bins=bins,
                density=True,
                histtype="step",
                linewidth=2,
                color=color,
                label=f"{label} (n={len(values)})",
            )
        axis.set_title(MODEL_NAMES[name])
        axis.set_xlabel("ALL-class model score (not calibrated probability)")
        axis.grid(alpha=0.2)
        axis.legend(frameon=False, fontsize=8)
    axes[0].set_ylabel("Density within dataset-label group")
    fig.suptitle("Saved validation score distributions and candidate policy band", fontsize=13)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    return fig


def policy_outcomes(run: dict) -> list[dict]:
    result = []
    for label, is_all in [("all", True), ("hem", False)]:
        mask = run["truth"] == is_all
        class_scores = run["scores"][mask]
        low = int(np.sum(class_scores < OPTION_B_V1.lower))
        inconclusive = int(
            np.sum((class_scores >= OPTION_B_V1.lower) & (class_scores < OPTION_B_V1.upper))
        )
        review = int(np.sum(class_scores >= OPTION_B_V1.upper))
        result.append(
            {
                "actual_label": label,
                "sample_count": int(mask.sum()),
                "analysis_complete_low_score": low,
                "analysis_complete_low_score_fraction": low / int(mask.sum()),
                "inconclusive": inconclusive,
                "inconclusive_fraction": inconclusive / int(mask.sum()),
                "review_required": review,
                "review_required_fraction": review / int(mask.sum()),
            }
        )
    return result


def plot_policy_outcomes(outcomes: list[dict], output: Path) -> plt.Figure:
    fig, axis = plt.subplots(figsize=(8.5, 4.6), constrained_layout=True)
    names = ["ALL-labeled images", "HEM-labeled images"]
    colors = ["#4b9c72", "#efbd4a", "#d96b5f"]
    labels = [
        f"Low score (<{OPTION_B_V1.lower:.2f})",
        f"Inconclusive ({OPTION_B_V1.lower:.2f}–<{OPTION_B_V1.upper:.2f})",
        f"Review required (≥{OPTION_B_V1.upper:.2f})",
    ]
    fields = ["analysis_complete_low_score", "inconclusive", "review_required"]
    bottoms = np.zeros(2)
    for field, color, label in zip(fields, colors, labels, strict=True):
        values = np.array([row[field] for row in outcomes], dtype=float)
        totals = np.array([row["sample_count"] for row in outcomes], dtype=float)
        heights = values / totals
        bars = axis.bar(names, heights, bottom=bottoms, color=color, label=label, width=0.58)
        for bar, count, total, bottom in zip(bars, values, totals, bottoms, strict=True):
            if count:
                height = count / total
                label_text = f"{int(count)}\n({height:.1%})" if height >= 0.075 else f"{int(count)}"
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    bottom + height / 2,
                    label_text,
                    ha="center",
                    va="center",
                    fontsize=9 if height >= 0.075 else 7,
                    color="#18212b",
                )
        bottoms += heights
    for index, row in enumerate(outcomes):
        axis.text(index, 1.015, f"n={row['sample_count']}", ha="center", fontsize=9)
    axis.set_ylim(0, 1.1)
    axis.set_ylabel("Share within dataset-label group")
    axis.set_title(
        "Current Option B status distribution on validation\n(lower-learning-rate checkpoint only)"
    )
    axis.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=1, fontsize=8)
    axis.grid(axis="y", alpha=0.2)
    fig.savefig(output, dpi=220, bbox_inches="tight")
    return fig


def dependency_group_rows(runs: dict, groups: dict) -> list[dict]:
    result = []
    for name, run in runs.items():
        grouped = defaultdict(list)
        for row in run["rows"]:
            grouped[groups[row["image_path"]]["dependency_group"]].append(row)
        for group, rows in sorted(grouped.items()):
            labels = {row["actual_label"] for row in rows}
            if len(labels) != 1:
                raise ValueError(f"Dependency group {group} has mixed labels.")
            label = next(iter(labels))
            if label == "all":
                errors = sum(float(row["all_score"]) < 0.5 for row in rows)
                error_name = "false_negative"
            else:
                errors = sum(float(row["all_score"]) >= 0.5 for row in rows)
                error_name = "false_positive"
            result.append(
                {
                    "dependency_group": group,
                    "member_subject_ids": ";".join(
                        sorted({groups[row["image_path"]]["subject_id"] for row in rows})
                    ),
                    "actual_label": label,
                    "model": name,
                    "image_count": len(rows),
                    "error_count": int(errors),
                    "error_type": error_name,
                    "error_rate": errors / len(rows),
                }
            )
    return result


def plot_group_errors(group_rows: list[dict], output: Path) -> plt.Figure:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)
    for axis, label, title in [
        (axes[0], "all", "ALL-labeled groups: missed ALL fraction"),
        (axes[1], "hem", "HEM-labeled groups: flagged HEM fraction"),
    ]:
        subset = [row for row in group_rows if row["actual_label"] == label]
        group_ids = sorted({row["dependency_group"] for row in subset})
        x = np.arange(len(group_ids))
        width = 0.36
        for offset, model in [(-width / 2, "grouped_baseline"), (width / 2, "lower_learning_rate")]:
            lookup = {row["dependency_group"]: row for row in subset if row["model"] == model}
            values = [lookup[group]["error_rate"] for group in group_ids]
            bars = axis.bar(
                x + offset, values, width, color=COLORS[model], label=MODEL_NAMES[model]
            )
            for bar, group in zip(bars, group_ids, strict=True):
                row = lookup[group]
                axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.012,
                    f"{row['error_count']}/{row['image_count']}",
                    ha="center",
                    va="bottom",
                    rotation=90,
                    fontsize=7,
                )
        axis.set_xticks(x, labels=group_ids, rotation=40, ha="right")
        axis.set_ylim(0, 1.18)
        axis.set_title(title)
        axis.set_ylabel("Error fraction within group")
        axis.grid(axis="y", alpha=0.2)
        axis.legend(frameon=False, fontsize=7)
    fig.suptitle(
        "Validation variation by dependency group at score cutoff 0.50\n"
        "(labels show errors / images)",
        fontsize=13,
    )
    fig.savefig(output, dpi=220, bbox_inches="tight")
    return fig


def build_report(
    runs: dict, groups: dict, group_rows: list[dict], outcomes: list[dict], output: Path
) -> dict:
    first = next(iter(runs.values()))
    split_sha = first["summary"]["split_sha256"]
    result = {
        "title": "HemoScope AI validation figures v1",
        "partition": "validation only",
        "validation_images": len(first["rows"]),
        "validation_subject_ids": len({row["subject_id"] for row in first["rows"]}),
        "validation_dependency_groups": len(
            {value["dependency_group"] for value in groups.values()}
        ),
        "split_manifest_sha256": split_sha,
        "test_predictions_or_metrics_used": False,
        "binary_cutoff": 0.5,
        "option_b": {
            "version": OPTION_B_V1.version,
            "bound_model_version": OPTION_B_V1.model_version,
            "bound_checkpoint_sha256": OPTION_B_V1.checkpoint_sha256,
            "lower_score_boundary": OPTION_B_V1.lower,
            "upper_score_boundary": OPTION_B_V1.upper,
            "validation_outcomes_lower_learning_rate_checkpoint": outcomes,
        },
        "models": {
            name: {
                "display_name": MODEL_NAMES[name],
                "checkpoint_sha256": run["summary"]["checkpoint_sha256"],
                "diagnostic_summary_sha256": sha256(run["summary_path"]),
                "prediction_file_sha256": sha256(run["predictions_path"]),
                "history_file_sha256": sha256(run["history_path"]),
                "best_epoch_by_validation_loss": run["best_epoch"],
                "validation_metrics_at_0_5": run["metrics"],
            }
            for name, run in runs.items()
        },
        "dependency_group_errors_at_0_5": group_rows,
        "interpretation_limits": [
            "The ALL score is a model score, not a calibrated disease probability.",
            "These are validation-cohort figures and do not estimate independent test performance.",
            "The Option B status chart reports outcomes by dataset label, not clinical status.",
            "Dependency groups are conservative image-relationship groups and are not confirmed "
            "patient identities.",
            "One run per configuration does not establish statistical significance "
            "or generalization "
            "to phone images.",
        ],
    }
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def write_markdown_report(runs: dict, outcomes: list[dict], output: Path) -> None:
    lines = [
        "# Validation figure review v1",
        "",
        "## Scope",
        "",
        "This report compares two saved grouped experiments on the same 1,486 validation images. "
        "It uses the saved scores and epoch histories only: no training, new inference, "
        "or test-set "
        "predictions or metrics were run. The test partition remains unexamined here.",
        "",
        "Both models use the same ten source subject IDs and nine conservative dependency groups. "
        "The dependency groups are image-relationship groupings, not verified patient identities.",
        "",
        "## Default cutoff comparison",
        "",
        "| Model | Weighted F1 | Sensitivity | Specificity | ROC AUC | "
        "ALL average precision | ALL missed | HEM flagged |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for name, run in runs.items():
        metrics = run["metrics"]
        lines.append(
            f"| {MODEL_NAMES[name]} | {metrics['weighted_f1']:.2%} | "
            f"{metrics['sensitivity']:.2%} | {metrics['specificity']:.2%} | "
            f"{metrics['roc_auc']:.4f} | {metrics['all_average_precision']:.4f} | "
            f"{metrics['false_negative']} / {metrics['all_count']} | "
            f"{metrics['false_positive']} / {metrics['hem_count']} |"
        )
    baseline = runs["grouped_baseline"]["metrics"]
    low_lr = runs["lower_learning_rate"]["metrics"]
    additional_misses = low_lr["false_negative"] - baseline["false_negative"]
    fewer_flags = baseline["false_positive"] - low_lr["false_positive"]
    lines.extend(
        [
            "",
            "At this cutoff, the lower learning rate has higher validation specificity "
            "and weighted F1, "
            f"but lower validation sensitivity: it misses {additional_misses} more "
            "ALL-labeled images "
            f"and flags {fewer_flags} fewer HEM-labeled images than the grouped baseline. "
            "This is an "
            "observed trade-off on one cohort, not a statistically established or independent "
            "improvement.",
            "",
            "## Option B status counts",
            "",
            "The current Option B boundaries are `<0.30` low score, `[0.30, 0.70)` inconclusive, "
            "and `>=0.70` review required. This policy is bound to the lower-learning-rate "
            "checkpoint "
            f"({OPTION_B_V1.checkpoint_sha256}). The ALL score is not a calibrated disease "
            "probability.",
            "",
            "| Dataset label | Images | Low score | Inconclusive | Review required |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in outcomes:
        total = row["sample_count"]
        lines.append(
            f"| {row['actual_label'].upper()} | {total} | "
            f"{row['analysis_complete_low_score']} "
            f"({row['analysis_complete_low_score_fraction']:.1%}) | "
            f"{row['inconclusive']} ({row['inconclusive_fraction']:.1%}) | "
            f"{row['review_required']} ({row['review_required_fraction']:.1%}) |"
        )
    deferred = sum(row["inconclusive"] for row in outcomes)
    n = sum(row["sample_count"] for row in outcomes)
    lines.extend(
        [
            "",
            f"Overall, {deferred} / {n} images ({deferred / n:.1%}) fall in the inconclusive band. "
            "The status counts are grouped by dataset label; they do not represent "
            "clinical outcomes.",
            "",
            "## Differences across dependency groups",
            "",
            "The group chart and `dependency-group-errors.csv` show each group's error fraction "
            "and count. The lower-rate model improves the HEM error fraction in each of the four "
            "HEM-labeled validation groups, while its ALL false-negative counts vary by group. "
            "For example, dependency group `dg_018` has 21 / 181 missed ALL images with the "
            "lower-rate model versus 2 / 181 with the grouped baseline. "
            "This group includes UID_33; "
            "it is a "
            "small number of validation groups, so the pattern needs more evidence "
            "before it guides "
            "another training change.",
            "",
            "## Limits and next checklist status",
            "",
            "These figures support interpretation of the grouped validation experiments. "
            "The validation cohort was used during model selection and policy exploration, "
            "so these are not final "
            "held-out estimates. No confidence intervals, multiple-seed estimate, independent "
            "challenge evaluation, or own-phone image evaluation is included. "
            "Do not use these figures as clinical "
            "performance evidence.",
            "",
            "Developer 1 Day 5's metrics-and-plots item is **partial**: the validation plots are "
            "now available, while final held-out evaluation remains pending. "
            "Day 4's own-phone evaluation "
            "also remains pending until separately labeled phone captures are available.",
            "",
            "## Figure files",
            "",
            "- `validation-figures.pdf`: all six figures.",
            "- `01_validation_progress.png`: validation loss and weighted F1 across epochs.",
            "- `02_roc_precision_recall.png`: discrimination curves.",
            "- `03_confusion_matrices.png`: errors at the default 0.50 score cutoff.",
            "- `04_score_distributions.png`: validation scores and the candidate policy band.",
            "- `05_option-b-status-distribution.png`: counts in each Option B status.",
            "- `06_dependency-group-error-rates.png`: errors by dependency group.",
            "",
            "Exact input/checkpoint hashes are recorded in `summary.json`.",
            "",
        ]
    )
    (output / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def create_figures(output: Path) -> None:
    ml_root = Path(__file__).resolve().parents[1]
    output = output.resolve()
    if output.exists():
        raise FileExistsError(f"Choose a new output directory; already exists: {output}")

    runs = {
        "grouped_baseline": load_run(
            "grouped_baseline",
            ml_root / "artifacts/diagnostics/grouped-v1-mps",
            ml_root / "artifacts/baseline-grouped-v1",
        ),
        "lower_learning_rate": load_run(
            "lower_learning_rate",
            ml_root / "artifacts/diagnostics/grouped-lowlr-v1-mps",
            ml_root / "artifacts/baseline-grouped-lowlr-v1",
        ),
    }
    if len({run["summary"]["split_sha256"] for run in runs.values()}) != 1:
        raise ValueError("Model diagnostics do not share the same validation split.")
    reference = next(iter(runs.values()))
    reference_rows = [
        (row["image_path"], row["subject_id"], row["actual_label"]) for row in reference["rows"]
    ]
    if any(
        [(row["image_path"], row["subject_id"], row["actual_label"]) for row in run["rows"]]
        != reference_rows
        for run in list(runs.values())[1:]
    ):
        raise ValueError("The compared models have different validation images or labels.")

    path_labels = {row["image_path"]: row["actual_label"] for row in reference["rows"]}
    manifest = ml_root / "artifacts/baseline-grouped-lowlr-v1/split-manifest.csv"
    groups = load_validation_groups(manifest, reference["summary"]["split_sha256"], path_labels)
    output.mkdir(parents=True)

    plot_definitions = [
        ("01_validation_progress.png", lambda path: plot_epoch_curves(runs, path)),
        ("02_roc_precision_recall.png", lambda path: plot_roc_pr(runs, path)),
        ("03_confusion_matrices.png", lambda path: plot_confusion_matrices(runs, path)),
    ]
    outcomes = policy_outcomes(runs["lower_learning_rate"])
    group_rows = dependency_group_rows(runs, groups)
    write_csv(output / "option-b-validation-outcomes.csv", outcomes)
    write_csv(output / "dependency-group-errors.csv", group_rows)
    plot_definitions.extend(
        [
            ("04_score_distributions.png", lambda path: plot_score_distributions(runs, path)),
            (
                "05_option-b-status-distribution.png",
                lambda path: plot_policy_outcomes(outcomes, path),
            ),
            (
                "06_dependency-group-error-rates.png",
                lambda path: plot_group_errors(group_rows, path),
            ),
        ]
    )

    with PdfPages(output / "validation-figures.pdf") as pdf:
        for filename, draw in plot_definitions:
            fig = draw(output / filename)
            pdf.savefig(fig, bbox_inches="tight")
        plt.close("all")

    report = build_report(runs, groups, group_rows, outcomes, output)
    write_markdown_report(runs, outcomes, output)
    (output / "README.md").write_text(
        "# Validation figures v1\n\n"
        "These figures use only the saved validation predictions for the two grouped runs. "
        "Both runs use the same 1,486 validation images, 10 source subject IDs and 9 "
        "dependency groups. The frozen split SHA-256 and source-file hashes are in "
        "`summary.json`.\n\n"
        "## Files\n\n"
        "- `validation-figures.pdf`: six-page report.\n"
        "- `01_validation_progress.png`: validation loss and weighted F1 by epoch; stars mark "
        "the checkpoint selected by lowest validation loss. Training loss was not saved, "
        "so it is not shown.\n"
        "- `02_roc_precision_recall.png`: ranking curves from validation ALL scores.\n"
        "- `03_confusion_matrices.png`: counts and row percentages at the default 0.50 "
        "score cutoff.\n"
        "- `04_score_distributions.png`: ALL-score distributions by dataset label "
        "with the candidate "
        "Option B band shown. Scores are not probabilities.\n"
        "- `05_option-b-status-distribution.png`: validation label counts across the current "
        "candidate's "
        "three Option B statuses.\n"
        "- `06_dependency-group-error-rates.png`: false-negative/false-positive fractions for each "
        "validation dependency group at 0.50; annotations show errors/images.\n"
        "- `option-b-validation-outcomes.csv` and `dependency-group-errors.csv`: chart source "
        "tables.\n"
        "- `summary.json`: model hashes, validation metrics, input hashes and limitations.\n\n"
        "The ALL score is not calibrated as a disease probability. The status chart reflects "
        "dataset labels, not patient diagnoses. These figures do not use test predictions or "
        "provide independent, clinical, or phone-camera performance evidence. Dependency groups "
        "are conservative image-relationship groups, not confirmed patient identities.\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"output": str(output), "models": report["models"], "option_b": report["option_b"]},
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/diagnostics/validation-figures-v1"),
        help="New output directory under ml/ (must not already exist).",
    )
    args = parser.parse_args()
    output = (
        args.output
        if args.output.is_absolute()
        else Path(__file__).resolve().parents[1] / args.output
    )
    create_figures(output)


if __name__ == "__main__":
    main()
