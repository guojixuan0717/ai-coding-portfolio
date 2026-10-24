"""独立手算预期与性质测试；不使用参考实现生成预期值。"""

import copy
import importlib
import json
import os
import unittest


_variant = os.environ.get("AI_PORTFOLIO_IMPL", "reference")
if _variant in ("reference", "starter"):
    solve = importlib.import_module(f".{_variant}", __package__).solve
elif _variant in ("mutant_transposed", "mutant_weighted_macro", "mutant_drop_unused"):
    solve = getattr(importlib.import_module(".mutants", __package__), _variant)
else:
    raise ValueError(f"Unknown AI_PORTFOLIO_IMPL: {_variant!r}")


class MetricsTests(unittest.TestCase):
    def assert_metrics(self, result, labels, matrix, rows, macro, micro):
        """rows: 手算的 (support, precision, recall, f1)，按 labels 排序。"""
        self.assertIs(type(result), dict)
        self.assertEqual(set(result), {
            "labels", "confusion_matrix", "per_class", "macro_f1", "micro_f1"
        })
        self.assertIs(type(result["labels"]), list)
        self.assertEqual(result["labels"], labels)
        self.assertIs(type(result["confusion_matrix"]), list)
        self.assertEqual(result["confusion_matrix"], matrix)
        for row in result["confusion_matrix"]:
            self.assertIs(type(row), list)
            self.assertEqual(len(row), len(labels))
            for value in row:
                self.assertIs(type(value), int)
                self.assertGreaterEqual(value, 0)
        self.assertIs(type(result["per_class"]), list)
        self.assertEqual(len(result["per_class"]), len(labels))
        for label, expected, actual in zip(labels, rows, result["per_class"]):
            self.assertIs(type(actual), dict)
            self.assertEqual(set(actual), {"label", "support", "precision", "recall", "f1"})
            self.assertIs(type(actual["label"]), str)
            self.assertEqual(actual["label"], label)
            self.assertIs(type(actual["support"]), int)
            self.assertEqual(actual["support"], expected[0])
            for key, value in zip(("precision", "recall", "f1"), expected[1:]):
                self.assertIs(type(actual[key]), float)
                self.assertAlmostEqual(actual[key], value, delta=1e-12)
        for key, expected in (("macro_f1", macro), ("micro_f1", micro)):
            self.assertIs(type(result[key]), float)
            self.assertAlmostEqual(result[key], expected, delta=1e-12)
        self.assertEqual(json.loads(json.dumps(result)), result)

    def test_perfect_prediction(self):
        self.assert_metrics(
            solve(["a", "b", "a"], ["a", "b", "a"], ["a", "b"]),
            ["a", "b"], [[2, 0], [0, 1]],
            [(2, 1.0, 1.0, 1.0), (1, 1.0, 1.0, 1.0)], 1.0, 1.0,
        )

    def test_hand_calculated_three_class(self):
        self.assert_metrics(
            solve(["cat", "cat", "cat", "cat", "dog", "dog", "bird"],
                  ["cat", "cat", "cat", "dog", "cat", "bird", "bird"],
                  ["cat", "dog", "bird"]),
            ["cat", "dog", "bird"], [[3, 1, 0], [1, 0, 1], [0, 0, 1]],
            [(4, 3 / 4, 3 / 4, 3 / 4), (2, 0.0, 0.0, 0.0),
             (1, 1 / 2, 1.0, 2 / 3)], 17 / 36, 4 / 7,
        )

    def test_label_order_controls_axes(self):
        self.assert_metrics(
            solve(["a", "a", "b"], ["a", "b", "b"], ["b", "a", "c"]),
            ["b", "a", "c"], [[1, 0, 0], [1, 1, 0], [0, 0, 0]],
            [(1, 1 / 2, 1.0, 2 / 3), (2, 1.0, 1 / 2, 2 / 3),
             (0, 0.0, 0.0, 0.0)], 4 / 9, 2 / 3,
        )

    def test_unused_class_in_macro_average(self):
        self.assert_metrics(
            solve(["a"], ["a"], ["a", "b", "c"]),
            ["a", "b", "c"], [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
            [(1, 1.0, 1.0, 1.0), (0, 0.0, 0.0, 0.0),
             (0, 0.0, 0.0, 0.0)], 1 / 3, 1.0,
        )

    def test_zero_true_support(self):
        self.assert_metrics(
            solve(["a", "a"], ["a", "b"], ["a", "b"]),
            ["a", "b"], [[1, 1], [0, 0]],
            [(2, 1.0, 1 / 2, 2 / 3), (0, 0.0, 0.0, 0.0)], 1 / 3, 1 / 2,
        )

    def test_zero_prediction_support(self):
        self.assert_metrics(
            solve(["a", "b", "b"], ["a", "a", "a"], ["a", "b"]),
            ["a", "b"], [[1, 0], [2, 0]],
            [(1, 1 / 3, 1.0, 1 / 2), (2, 0.0, 0.0, 0.0)], 1 / 4, 1 / 3,
        )

    def test_all_predictions_wrong(self):
        self.assert_metrics(
            solve(["a", "b", "c"], ["b", "c", "a"], ["a", "b", "c"]),
            ["a", "b", "c"], [[0, 1, 0], [0, 0, 1], [1, 0, 0]],
            [(1, 0.0, 0.0, 0.0)] * 3, 0.0, 0.0,
        )

    def test_empty_observations(self):
        self.assert_metrics(
            solve([], [], ["x", "y"]),
            ["x", "y"], [[0, 0], [0, 0]],
            [(0, 0.0, 0.0, 0.0)] * 2, 0.0, 0.0,
        )

    def test_unequal_support_uses_macro_average(self):
        self.assert_metrics(
            solve(["a"] * 8 + ["b"] * 2, ["a"] * 10, ["a", "b"]),
            ["a", "b"], [[8, 0], [2, 0]],
            [(8, 4 / 5, 1.0, 8 / 9), (2, 0.0, 0.0, 0.0)], 4 / 9, 4 / 5,
        )

    def test_single_class(self):
        self.assert_metrics(
            solve(["", "", ""], ["", "", ""], [""]),
            [""], [[3]], [(3, 1.0, 1.0, 1.0)], 1.0, 1.0,
        )

    def test_tuple_inputs(self):
        self.assert_metrics(
            solve(("b", "a"), ("a", "a"), ("b", "a")),
            ["b", "a"], [[0, 1], [0, 1]],
            [(1, 0.0, 0.0, 0.0), (1, 1 / 2, 1.0, 2 / 3)], 1 / 3, 1 / 2,
        )

    def test_inputs_unmutated_on_success(self):
        args = [["a", "b", "a"], ["b", "b", "a"], ["b", "a"]]
        original = copy.deepcopy(args)
        result = solve(*args)
        self.assertEqual(args, original)
        self.assertIsNot(result["labels"], args[2])
        result["labels"].append("new")
        old_other_row = list(result["confusion_matrix"][1])
        result["confusion_matrix"][0][0] = 99
        self.assertEqual(result["confusion_matrix"][1], old_other_row)
        self.assertEqual(args, original)

    def test_inputs_unmutated_on_failure(self):
        args = [["a", "unknown"], ["a", "a"], ["a", "b"]]
        original = copy.deepcopy(args)
        with self.assertRaises(ValueError):
            solve(*args)
        self.assertEqual(args, original)

    def test_length_mismatch(self):
        for truth, prediction in ((["a"], []), ([], ["a"]), (["a", "a"], ["a"])):
            with self.subTest(truth=truth, prediction=prediction):
                with self.assertRaises(ValueError):
                    solve(truth, prediction, ["a"])
        # 先验证长度，再逐个检查观察值类型。
        with self.assertRaises(ValueError):
            solve([None], [], ["a"])

    def test_unknown_true_label(self):
        for unknown in ("missing", "A", " a"):
            with self.subTest(unknown=unknown):
                with self.assertRaises(ValueError):
                    solve([unknown], ["a"], ["a"])
        # y_true 的未知类别必须先于 y_pred 的类型错误被发现。
        with self.assertRaises(ValueError):
            solve(["missing"], [None], ["a"])

    def test_unknown_predicted_label(self):
        for unknown in ("missing", "A", "a "):
            with self.subTest(unknown=unknown):
                with self.assertRaises(ValueError):
                    solve(["a"], [unknown], ["a"])

    def test_duplicate_and_empty_labels(self):
        for labels in ([], (), ["a", "a"], ("a", "b", "a")):
            with self.subTest(labels=labels):
                with self.assertRaises(ValueError):
                    solve([], [], labels)

    def test_reject_invalid_containers(self):
        class ListSubclass(list):
            pass

        class TupleSubclass(tuple):
            pass

        invalid = (None, "a", {"a"}, {"a": 1}, iter(["a"]), range(1),
                   ListSubclass(["a"]), TupleSubclass(("a",)))
        for position in range(3):
            for value in invalid:
                args = [["a"], ["a"], ["a"]]
                args[position] = value
                with self.subTest(position=position, kind=type(value).__name__):
                    with self.assertRaises(TypeError):
                        solve(*args)
        # 三个容器的类型检查先于 labels 非空检查。
        with self.assertRaises(TypeError):
            solve(None, [], [])

    def test_reject_non_string_elements(self):
        class StringSubclass(str):
            pass

        for position in range(3):
            for value in (True, 1, 1.0, None, [], StringSubclass("a")):
                args = [["a"], ["a"], ["a"]]
                args[position] = [value]
                with self.subTest(position=position, kind=type(value).__name__):
                    with self.assertRaises(TypeError):
                        solve(*args)
        # labels 元素类型先于观察值长度检查。
        with self.assertRaises(TypeError):
            solve([], ["a"], [1])

    def test_duplication_invariance(self):
        # 将两个正确样本及一个错误样本重复三遍：计数扩大，所有比率不变。
        truth = ["a", "a", "b"] * 3
        prediction = ["a", "b", "b"] * 3
        self.assert_metrics(
            solve(truth, prediction, ["a", "b"]),
            ["a", "b"], [[3, 3], [0, 3]],
            [(6, 1.0, 1 / 2, 2 / 3), (3, 1 / 2, 1.0, 2 / 3)], 2 / 3, 2 / 3,
        )


if __name__ == "__main__":
    unittest.main()
