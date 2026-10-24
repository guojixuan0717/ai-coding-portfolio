# T03：单标签多分类评测器

本任务是于 2026-10-24 新生成的 AI 辅助作品样例，所有示例数据均为人工合成。它展示任务规范、参考实现、评测与错误定位的设计方式，不代表申请人既往项目、工作经历、学历或官方认证。学习者应理解代码、独立完成候选实现并如实说明 AI 辅助情况。

## 任务目标

实现 Python 3.10+ 函数 `solve(y_true, y_pred, labels)`，对单标签多分类预测计算混淆矩阵、各类别的 precision / recall / F1、macro-F1 和 micro-F1。只允许 Python 标准库，不访问网络、文件、系统时间或随机数。

## 输入及验证契约

- 三个参数的容器类型必须恰好为 `list` 或 `tuple`，不接受字符串、集合、迭代器以及这些容器的子类。违反时抛出 `TypeError`。
- 所有元素类型必须恰好为 `str`，不接受数值、布尔值、`None` 或字符串子类。空字符串也是合法类别名。
- `labels` 必须非空、无重复；否则抛出 `ValueError`。大小写敏感，不清洗、排序或合并类别名。
- `y_true` 和 `y_pred` 长度必须相等，允许同时为空；长度不同抛出 `ValueError`。
- 每个观察值必须存在于显式给出的 `labels` 中，未知真实标签或预测标签均抛出 `ValueError`。
- 为使多个错误同时存在时也可复现，按如下次序验证：三个容器类型 → `labels` 非空 → `labels` 元素类型 → `labels` 唯一性 → 观察值长度 → `y_true` 各元素的类型和成员资格 → `y_pred` 各元素的类型和成员资格。
- 成功或抛出异常时均不得改变输入。返回结构必须是新建的，不得将输入列表直接放入结果。异常文本不评分。

## 输出结构

返回普通 `dict`，恰好包含以下五个键：

```text
{
  "labels": list[str],
  "confusion_matrix": list[list[int]],
  "per_class": list[{
      "label": str,
      "support": int,
      "precision": float,
      "recall": float,
      "f1": float
  }],
  "macro_f1": float,
  "micro_f1": float
}
```

`labels` 与 `per_class` 都严格保持输入 `labels` 的顺序。混淆矩阵为 K×K，**行表示真实类别，列表示预测类别**。即使类别没有任何观察值，也必须保留该行、列以及对应的 `per_class` 项。矩阵计数与 `support` 必须为普通非负 `int`，所有指标均为普通 `float`；不舍入，浮点比较容差采用 `1e-12`。返回值可直接 JSON 序列化。

设 `C[i][j]` 为混淆矩阵。类别 i 的：

- `TPᵢ = C[i][i]`；`supportᵢ = Σⱼ C[i][j]`。
- `FPᵢ = Σⱼ C[j][i] − TPᵢ`；`FNᵢ = supportᵢ − TPᵢ`。
- `precisionᵢ = TPᵢ / (TPᵢ + FPᵢ)`。
- `recallᵢ = TPᵢ / (TPᵢ + FNᵢ)`。
- `F1ᵢ = 2TPᵢ / (2TPᵢ + FPᵢ + FNᵢ)`。
- `macro_f1 = (Σᵢ F1ᵢ) / K`，包括所有显式声明但未出现的类别，不按 `support` 加权。
- `micro_f1 = 2Σᵢ TPᵢ / (2Σᵢ TPᵢ + Σᵢ FPᵢ + Σᵢ FNᵢ)`；本任务为单标签多分类，因此非空数据时等于预测正确数除以样本总数。

**零除规则：每个指标的分母为零时，该指标必须返回 `0.0`。** 两组观察值同时为空且类别列表非空时，所有计数与指标均为零。

## 示例一：非对称错误及未使用类别

```python
solve(["a", "a", "b"], ["a", "b", "b"], ["b", "a", "c"])
```

精确输出（键顺序无要求）：

```json
{
  "labels": ["b", "a", "c"],
  "confusion_matrix": [[1, 0, 0], [1, 1, 0], [0, 0, 0]],
  "per_class": [
    {"label": "b", "support": 1, "precision": 0.5, "recall": 1.0, "f1": 0.6666666666666666},
    {"label": "a", "support": 2, "precision": 1.0, "recall": 0.5, "f1": 0.6666666666666666},
    {"label": "c", "support": 0, "precision": 0.0, "recall": 0.0, "f1": 0.0}
  ],
  "macro_f1": 0.4444444444444444,
  "micro_f1": 0.6666666666666666
}
```

## 示例二：空观察值

```python
solve([], [], ["x"])
# {"labels": ["x"], "confusion_matrix": [[0]],
#  "per_class": [{"label": "x", "support": 0, "precision": 0.0,
#                 "recall": 0.0, "f1": 0.0}],
#  "macro_f1": 0.0, "micro_f1": 0.0}
```

## 交付与评测

将实现写入 `starter.py` 的 `solve`。`reference.py` 是可审阅的参考答案；`mutants.py` 包含三个有意植入错误的实现，仅用于检验测试是否能识别常见错误。故障实现复用参考答案中未改动的行为，以隔离矩阵转置、误用加权平均、忽略未出现类别三种错误；它们不是独立的性能基线。20 个独立测试方法各 5 分，共 100 分；具体映射见 `rubric.json`。测试预期使用手工计算和指标性质，不调用参考答案生成预期值。

从作品集根目录运行：

```powershell
python -m unittest tasks.t03_metrics.test_task -v
$env:AI_PORTFOLIO_IMPL = "starter"
python -m unittest tasks.t03_metrics.test_task -v
# 检查故障实现时改为 mutant_transposed、mutant_weighted_macro 或 mutant_drop_unused。
Remove-Item Env:AI_PORTFOLIO_IMPL
```

环境变量未设置时测试 `reference`。未知实现名明确报错。由于提供完整矩阵，时间复杂度目标为 `O(N + K²)`，空间复杂度为 `O(K²)`（返回数据计入）；K 为类别数，N 为样本数。无需支持超出内存容量的数据。该评测只覆盖本函数契约，不能单独证明生产环境经验或确保任何平台审核通过。
