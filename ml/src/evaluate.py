from __future__ import annotations


def compute_metrics(
    y_true: list[int],
    y_pred: list[int],
    *,
    positive_class: int = 1,
) -> dict[str, object]:
    try:
        from sklearn.metrics import confusion_matrix, f1_score
    except ImportError as exc:
        raise RuntimeError(
            'Install the ML training dependencies with: python -m pip install -e ".[train]"'
        ) from exc

    labels = sorted(set(y_true) | set(y_pred))
    matrix = confusion_matrix(y_true, y_pred, labels=labels)
    weighted_f1 = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
    if positive_class not in labels:
        sensitivity = None
        specificity = None
    else:
        positive_index = labels.index(positive_class)
        true_positive = int(matrix[positive_index, positive_index])
        false_negative = int(matrix[positive_index, :].sum() - true_positive)
        false_positive = int(matrix[:, positive_index].sum() - true_positive)
        true_negative = int(matrix.sum() - true_positive - false_negative - false_positive)
        sensitivity = (
            true_positive / (true_positive + false_negative)
            if true_positive + false_negative
            else None
        )
        specificity = (
            true_negative / (true_negative + false_positive)
            if true_negative + false_positive
            else None
        )
    return {
        "sample_count": len(y_true),
        "class_labels": labels,
        "confusion_matrix": matrix.tolist(),
        "weighted_f1": weighted_f1,
        "sensitivity": sensitivity,
        "specificity": specificity,
    }
