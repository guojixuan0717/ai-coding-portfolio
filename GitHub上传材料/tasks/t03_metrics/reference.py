"""确定性单标签多分类评测的参考实现，仅依赖 Python 标准库。"""


def solve(y_true, y_pred, labels):
    """按 SPEC.md 返回混淆矩阵及分类指标；不修改任何输入。"""
    for name, values in (("y_true", y_true), ("y_pred", y_pred), ("labels", labels)):
        if type(values) not in (list, tuple):
            raise TypeError(f"{name} must be a list or tuple")

    if not labels:
        raise ValueError("labels must not be empty")
    if any(type(label) is not str for label in labels):
        raise TypeError("all labels must be strings")
    if len(set(labels)) != len(labels):
        raise ValueError("labels must be unique")
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have equal lengths")

    index = {label: i for i, label in enumerate(labels)}
    for name, values in (("y_true", y_true), ("y_pred", y_pred)):
        for value in values:
            if type(value) is not str:
                raise TypeError(f"all {name} elements must be strings")
            if value not in index:
                raise ValueError(f"unknown label in {name}: {value!r}")

    size = len(labels)
    matrix = [[0] * size for _ in range(size)]
    for truth, prediction in zip(y_true, y_pred):
        matrix[index[truth]][index[prediction]] += 1

    true_support = [sum(row) for row in matrix]
    pred_support = [sum(matrix[row][column] for row in range(size))
                    for column in range(size)]
    per_class = []
    f1_total = 0.0
    true_positives = 0
    for i, label in enumerate(labels):
        tp = matrix[i][i]
        fp = pred_support[i] - tp
        fn = true_support[i] - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0
        per_class.append({
            "label": label,
            "support": true_support[i],
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })
        f1_total += f1
        true_positives += tp

    count = len(y_true)
    return {
        "labels": list(labels),
        "confusion_matrix": matrix,
        "per_class": per_class,
        "macro_f1": f1_total / size,
        "micro_f1": true_positives / count if count else 0.0,
    }
