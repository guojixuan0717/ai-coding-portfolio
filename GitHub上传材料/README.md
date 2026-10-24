# AI Coding 任务设计实作作品集

[阅读作品集 PDF](AI_Coding_任务设计作品集.pdf) · [查看实际运行报告](reports/evaluation.md) · [材料来源与 AI 辅助说明](docs/PROVENANCE.md)

本目录已整理为可直接上传 GitHub 的仓库根目录。请上传本目录内部的文件与子文件夹，保持 `tasks`、`docs`、`reports` 的层级。当前仅完成本地整理，尚未创建或发布远程仓库，也没有可填写的公开链接。

PDF 用于快速阅读，下面的源码与测试可直接在仓库内查看。`申请填写参考.txt` 是表单填写指引，不是官方证明或认证。个人复现记录仍应根据实际操作填写。

本仓库是一组新建的、经 AI 辅助生成的 Python 任务设计样例，面向截图中选择的「Vibe Coding AI Coding 任务设计专家」方向。它展示任务规格、参考实现、测试、评分与缺陷定位的组织方式。它不证明申请人已有专家资历、商业项目经历或独立完成能力，也不代表 TalentsAI 认可。

## 快速复现

需要 Python 3.10 或更新版本，无第三方依赖、无网络请求。进入包含本 README 的目录后执行：

```text
python evaluate.py
```

Windows 如未配置 python，可尝试 `py -3 evaluate.py`。成功时退出码为 0，并更新 `reports/evaluation.json` 与 `reports/evaluation.md`。参考实现应全通过；起始桩未完成和错误候选测试失败是预期现象。注意这只是本作品集的检查规则，不是平台通过标准。

可单独运行一题参考实现：

```text
python -m unittest tasks.t01_dedup.test_task -v
python -m unittest tasks.t02_split.test_task -v
python -m unittest tasks.t03_metrics.test_task -v
```

## 三个任务

| 目录 | 主题 | 设计关注点 |
|---|---|---|
| tasks/t01_dedup | 训练记录去重 | Unicode 归一化、稳定顺序、严格输入与不修改原始数据 |
| tasks/t02_split | 按组划分数据集 | 同组隔离、可复现排序、分组比例与记录比例的区别 |
| tasks/t03_metrics | 多分类评估 | 混淆矩阵方向、零分母、宏平均与微平均、标签顺序 |

每题含 `SPEC.md`、`starter.py`、`reference.py`、`test_task.py`、`mutants.py` 和 `rubric.json`。`starter.py` 留给练习者实现；`reference.py` 提供公开参考答案。所有输入均为合成样例，没有真实用户数据。

## 证据如何解释

- `reports/evaluation.json` 保存实际测试日志、每个测试方法状态和源码 SHA256；机器结果可重跑核对。
- `reports/evaluation.md` 是供人阅读的摘要。方法内部的子测试不计为额外测试方法。
- `mutants.py` 是人为编写的典型错误，并非对真实 AI 模型的实测。发现这些错误不能表示测试完备。
- 三题的评分都是样例规则，每题 100 分，不是官方评分，也不设置「专家通过线」。
- 本包公开包含测试与答案，不能直接用作保密考试。正式评估须另建未泄露的测试集，并在独立、隔离的环境执行候选代码。

## 申请前建议完成

1. 阅读三题规格，先不看参考答案，独立实现至少一题的 starter。
2. 亲自运行评估，保存实际输出。以自己的修改为依据记录贡献，不把本次生成内容写为既往独立项目。
3. 为每题补充一个未包含的新边界案例，说明为什么现有测试可能遗漏它。
4. 完成 `docs/PERSONAL_REVIEW.md` 中的讲解与贡献记录。只有实际完成的项目可写入个人说明。
5. 如需链接，发布到自己的真实代码仓库并验证访问权限；没有发布时不要提交虚构地址。

## 阅读路线

先读 `docs/DESIGN.md`，再读任一题的 `SPEC.md`、测试和参考实现，最后查看评估报告。`docs/PROVENANCE.md` 说明材料来源与 AI 辅助范围。
