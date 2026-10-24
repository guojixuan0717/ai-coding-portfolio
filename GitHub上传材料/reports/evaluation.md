# 本地可复现评估报告

运行时间：2026-10-24T14:59:45+08:00；Python 3.12.14。

本报告由 evaluate.py 实际运行生成。它仅评价本包内的参考实现、起始桩和人为编写的错误候选，不能推断官方审核结果、用户个人能力或真实模型表现。

计数单位为 unittest 测试方法；方法内部的子测试不另外计数。每题的 100 分是样例评分，不是平台官方标准。

| 任务 | 候选 | 通过方法数 | 样例分数 |
|---|---|---:|---:|
| t01_dedup | reference | 20/20 | 100/100 |
| t01_dedup | starter | 0/20 | 0/100 |
| t01_dedup | mutant_last_wins | 13/20 | 65/100 |
| t01_dedup | mutant_lowercase | 19/20 | 95/100 |
| t01_dedup | mutant_first_field | 18/20 | 90/100 |
| t02_split | reference | 20/20 | 100/100 |
| t02_split | starter | 0/20 | 0/100 |
| t02_split | mutant_row_split | 11/20 | 55/100 |
| t02_split | mutant_bankers_rounding | 18/20 | 90/100 |
| t02_split | mutant_first_seen_groups | 12/20 | 60/100 |
| t03_metrics | reference | 20/20 | 100/100 |
| t03_metrics | starter | 0/20 | 0/100 |
| t03_metrics | mutant_transposed | 11/20 | 55/100 |
| t03_metrics | mutant_weighted_macro | 14/20 | 70/100 |
| t03_metrics | mutant_drop_unused | 18/20 | 90/100 |

参考实现通过 60/60 个测试方法。
发现 9/9 个预设错误候选。发现表示至少一个测试方法失败，不表示完整缺陷覆盖。

JSON 同时保留每个方法的状态、原始测试日志、运行环境和源码 SHA256。重新运行会更新本报告。

测试和错误解法为同一作品集共同设计，存在共同盲区。未进行真实模型对比、性能基准、独立审核或保密测试。
