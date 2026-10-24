"""Reproduce local task checks without network or third-party packages.

This runner evaluates the bundled reference, starter and deliberate faulty
implementations. It does not evaluate a language model or official assessment.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import unittest
from datetime import datetime, timedelta, timezone

ROOT = Path(__file__).resolve().parent
TASKS = ("t01_dedup", "t02_split", "t03_metrics")


def snapshot() -> dict[str, str]:
    """Hash source, specs and rubric, excluding generated reports and caches."""
    files = [ROOT / "evaluate.py"]
    for task in TASKS:
        files.extend(p for p in (ROOT / "tasks" / task).iterdir()
                     if p.is_file() and p.suffix in {".py", ".md", ".json"})
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(files)}


def child(task: str, variant: str) -> int:
    os.environ["AI_PORTFOLIO_IMPL"] = variant
    module = importlib.import_module(f"tasks.{task}.test_task")
    rubric = json.loads((ROOT / "tasks" / task / "rubric.json").read_text("utf-8"))
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    stream = io.StringIO()

    class Capture(unittest.TextTestResult):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.outcomes: dict[str, dict] = {}

        def startTest(self, test):
            super().startTest(test)
            self.outcomes[test.id()] = {"name": test._testMethodName, "status": "passed"}

        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.outcomes[test.id()]["status"] = "failed"

        def addError(self, test, err):
            super().addError(test, err)
            self.outcomes[test.id()]["status"] = "error"

        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            self.outcomes[test.id()]["status"] = "skipped"

        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            if err is not None:
                self.outcomes[test.id()]["status"] = "failed"

        def addExpectedFailure(self, test, err):
            super().addExpectedFailure(test, err)
            self.outcomes[test.id()]["status"] = "expected_failure"

        def addUnexpectedSuccess(self, test):
            super().addUnexpectedSuccess(test)
            self.outcomes[test.id()]["status"] = "unexpected_success"

    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Capture).run(suite)
    outcomes = list(result.outcomes.values())
    names = [item["name"] for item in outcomes]
    weights = rubric["tests"]
    if len(names) != len(set(names)) or set(names) != set(weights):
        raise ValueError(f"{task}: rubric/test methods mismatch")
    if any(type(v) is not int or v <= 0 for v in weights.values()) or sum(weights.values()) != 100:
        raise ValueError(f"{task}: invalid rubric weights")
    for item in outcomes:
        item["points"] = weights[item["name"]]
        item["earned"] = item["points"] if item["status"] == "passed" else 0
    payload = {
        "task_id": task, "variant": variant, "test_methods": result.testsRun,
        "passed_methods": sum(i["status"] == "passed" for i in outcomes),
        "score": sum(i["earned"] for i in outcomes), "max_score": 100,
        "success": result.wasSuccessful() and all(i["status"] == "passed" for i in outcomes),
        "outcomes": outcomes, "unittest_log": stream.getvalue(),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0


def evaluate() -> int:
    started = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    hashes_before = snapshot()
    runs = []
    for task in TASKS:
        rubric = json.loads((ROOT / "tasks" / task / "rubric.json").read_text("utf-8"))
        variants = ["reference", "starter", *rubric["mutants"]]
        if not rubric["mutants"] or len(variants) != len(set(variants)):
            raise ValueError(f"{task}: empty or duplicate candidate list")
        for variant in variants:
            completed = subprocess.run(
                [sys.executable, str(ROOT / "evaluate.py"), "--child", task, variant],
                cwd=ROOT, capture_output=True, text=True, encoding="utf-8", timeout=45,
                env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"},
            )
            if completed.returncode != 0:
                raise RuntimeError(f"{task}/{variant} runner failed:\n{completed.stderr}")
            run = json.loads(completed.stdout)
            runs.append(run)
            print(f"{task:14} {variant:29} {run['passed_methods']:2}/{run['test_methods']:2} methods  {run['score']:3}/100")
    hashes_after = snapshot()
    if hashes_before != hashes_after:
        raise RuntimeError("Source changed during evaluation; rerun on stable files.")
    reference = [r for r in runs if r["variant"] == "reference"]
    mutants = [r for r in runs if r["variant"].startswith("mutant_")]
    starters = [r for r in runs if r["variant"] == "starter"]
    summary = {
        "reference_passed_methods": sum(r["passed_methods"] for r in reference),
        "reference_test_methods": sum(r["test_methods"] for r in reference),
        "references_all_pass": all(r["success"] for r in reference),
        "mutants_detected": sum(not r["success"] for r in mutants),
        "mutants_total": len(mutants),
        "starters_incomplete": all(not r["success"] for r in starters),
    }
    report = {
        "generated_at": started, "timezone": "UTC+08:00", "python": platform.python_version(),
        "platform": platform.platform(),
        "scope": "Local bundled unit tests and deliberately faulty candidates only. Not an official review or model evaluation.",
        "counting": "Counts are unittest methods; subtests or generated cases inside a method are not additional methods.",
        "scoring": "Illustrative task rubric only; no official pass threshold.",
        "source_sha256": hashes_after, "summary": summary, "runs": runs,
    }
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    (reports / "evaluation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# 本地可复现评估报告", "", f"运行时间：{started}；Python {report['python']}。", "",
             "本报告由 evaluate.py 实际运行生成。它仅评价本包内的参考实现、起始桩和人为编写的错误候选，不能推断官方审核结果、用户个人能力或真实模型表现。", "",
             "计数单位为 unittest 测试方法；方法内部的子测试不另外计数。每题的 100 分是样例评分，不是平台官方标准。", "",
             "| 任务 | 候选 | 通过方法数 | 样例分数 |", "|---|---|---:|---:|"]
    for r in runs:
        lines.append(f"| {r['task_id']} | {r['variant']} | {r['passed_methods']}/{r['test_methods']} | {r['score']}/100 |")
    lines.extend(["", f"参考实现通过 {summary['reference_passed_methods']}/{summary['reference_test_methods']} 个测试方法。",
                  f"发现 {summary['mutants_detected']}/{summary['mutants_total']} 个预设错误候选。发现表示至少一个测试方法失败，不表示完整缺陷覆盖。", "",
                  "JSON 同时保留每个方法的状态、原始测试日志、运行环境和源码 SHA256。重新运行会更新本报告。", "",
                  "测试和错误解法为同一作品集共同设计，存在共同盲区。未进行真实模型对比、性能基准、独立审核或保密测试。"])
    (reports / "evaluation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if summary["references_all_pass"] and summary["mutants_detected"] == summary["mutants_total"] and summary["starters_incomplete"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", nargs=2, metavar=("TASK", "VARIANT"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    raise SystemExit(child(*args.child) if args.child else evaluate())
