"""用于验证测试检错能力的故障实现，禁止作为正确答案提交。"""

from .reference import solve as _reference


def mutant_transposed(y_true, y_pred, labels):
    """常见错误：混淆真实标签与预测标签，使矩阵转置并交换精确率、召回率。"""
    return _reference(y_pred, y_true, labels)


def mutant_weighted_macro(y_true, y_pred, labels):
    """常见错误：将样本量加权 F1 当作 macro-F1。"""
    result = _reference(y_true, y_pred, labels)
    count = len(y_true)
    result["macro_f1"] = (
        sum(item["f1"] * item["support"] for item in result["per_class"]) / count
        if count else 0.0
    )
    return result


def mutant_drop_unused(y_true, y_pred, labels):
    """常见错误：计算 macro-F1 时忽略完全未出现的已声明类别。"""
    result = _reference(y_true, y_pred, labels)
    observed = set(y_true) | set(y_pred)
    used = [item["f1"] for item in result["per_class"] if item["label"] in observed]
    result["macro_f1"] = sum(used) / len(used) if used else 0.0
    return result
