"""Synthetic fixtures and independent expectations for the public task contract.

AI_PORTFOLIO_IMPL chooses reference (default), starter, or a named mutant.
No expected result is calculated by calling the reference implementation.
"""

import copy
import importlib
import os
import unittest


_variant = os.environ.get("AI_PORTFOLIO_IMPL", "reference")
if _variant in ("reference", "starter"):
    solve = importlib.import_module(f".{_variant}", __package__).solve
elif _variant in (
    "mutant_row_split", "mutant_bankers_rounding", "mutant_first_seen_groups"
):
    solve = getattr(importlib.import_module(".mutants", __package__), _variant)
else:
    raise ValueError(f"Unknown AI_PORTFOLIO_IMPL: {_variant!r}")


class SplitTaskTests(unittest.TestCase):
    def assert_partition(self, original, result):
        self.assertIsInstance(result, dict)
        self.assertEqual(set(result), {"train", "validation"})
        self.assertIsInstance(result["train"], list)
        self.assertIsInstance(result["validation"], list)
        self.assertEqual(len(result["train"]) + len(result["validation"]), len(original))
        train_groups = {r["group"] for r in result["train"]}
        validation_groups = {r["group"] for r in result["validation"]}
        self.assertTrue(train_groups.isdisjoint(validation_groups))
        for side, selected_groups in (
            ("train", train_groups), ("validation", validation_groups)
        ):
            expected = [r for r in original if r["group"] in selected_groups]
            self.assertEqual(result[side], expected)
            self.assertTrue(all(a is b for a, b in zip(result[side], expected)))

    def test_known_ascii_seed0(self):
        records = [{"group": g, "id": i} for i, g in enumerate("abcdef")]
        result = solve(records, 0.5)
        self.assertEqual([r["group"] for r in result["validation"]], ["b", "c", "e"])
        self.assertEqual([r["group"] for r in result["train"]], ["a", "d", "f"])
        self.assert_partition(records, result)

    def test_known_unicode_seed7(self):
        groups = ["项目甲", "项目乙", "Group A", "group a", " ", "é"]
        records = [{"group": g} for g in groups]
        result = solve(records, 0.5, 7)
        self.assertEqual([r["group"] for r in result["validation"]], ["项目甲", "项目乙", "é"])
        self.assertEqual([r["group"] for r in result["train"]], ["Group A", "group a", " "])
        self.assert_partition(records, result)

    def test_group_integrity_uneven_sizes(self):
        records = [{"group": "a", "id": i} for i in range(8)]
        records += [{"group": "b", "id": 8}, {"group": "c", "id": 9}, {"group": "b", "id": 10}]
        result = solve(records, 1 / 3)
        self.assertEqual([r["id"] for r in result["validation"]], [8, 10])
        self.assertEqual(len(result["train"]), 9)
        self.assert_partition(records, result)

    def test_half_up_rounding(self):
        records = [{"group": g} for g in "abc"]
        result = solve(records, 0.5)
        self.assertEqual([r["group"] for r in result["validation"]], ["b", "c"])
        self.assert_partition(records, result)

    def test_decimal_rounding_boundary(self):
        records = [{"group": g} for g in "abcde"]
        result = solve(records, 0.1)
        self.assertEqual([r["group"] for r in result["validation"]], ["e"])
        self.assert_partition(records, result)

    def test_zero_fraction(self):
        records = [{"group": "b"}, {"group": "a"}, {"group": "b"}]
        for fraction in (0, 0.0, -0.0):
            with self.subTest(fraction=fraction):
                result = solve(records, fraction, 19)
                self.assertEqual(result, {"train": records, "validation": []})
                self.assert_partition(records, result)

    def test_one_fraction(self):
        records = [{"group": "z"}, {"group": "a"}, {"group": "z"}]
        for fraction in (1, 1.0):
            with self.subTest(fraction=fraction):
                result = solve(records, fraction, -19)
                self.assertEqual(result, {"train": [], "validation": records})
                self.assert_partition(records, result)

    def test_empty_input(self):
        for fraction in (0, 0.5, 1):
            with self.subTest(fraction=fraction):
                result = solve([], fraction)
                self.assertEqual(result, {"train": [], "validation": []})
                self.assertIsNot(result["train"], result["validation"])

    def test_fresh_containers_and_original_objects(self):
        records = [{"group": "a", "payload": [1, {"x": 2}]}, {"group": "b", "payload": []}]
        before = copy.deepcopy(records)
        result = solve(records, 0.5)
        self.assertEqual(records, before)
        self.assertIsNot(result["train"], records)
        self.assertIsNot(result["validation"], records)
        self.assertIsNot(result["train"], result["validation"])
        self.assert_partition(records, result)
        again = solve(records, 0.5)
        self.assertIsNot(result, again)
        self.assertIsNot(result["train"], again["train"])
        self.assertIsNot(result["validation"], again["validation"])

    def test_relative_order_preserved(self):
        records = [{"group": g, "id": i} for i, g in enumerate("ecabfcdeba")]
        result = solve(records, 0.5)
        self.assertEqual([r["id"] for r in result["validation"]], [0, 1, 3, 5, 7, 8])
        self.assertEqual([r["id"] for r in result["train"]], [2, 4, 6, 9])
        self.assert_partition(records, result)

    def test_membership_independent_of_input_order(self):
        records = [{"group": g, "id": i} for i, g in enumerate("abcdefaabbcc")]
        expected_validation = {"b", "c", "e"}
        for rows in (records, list(reversed(records)), records[4:] + records[:4]):
            with self.subTest(ids=[r["id"] for r in rows]):
                result = solve(rows, 0.5)
                self.assertEqual({r["group"] for r in result["validation"]}, expected_validation)
                self.assert_partition(rows, result)

    def test_seed_controls_membership(self):
        records = [{"group": g} for g in "abcdef"]
        for seed, expected in ((0, {"b", "c", "e"}), (7, {"c", "d", "e"}), (-2, {"c", "e", "f"})):
            with self.subTest(seed=seed):
                result = solve(records, 0.5, seed)
                self.assertEqual({r["group"] for r in result["validation"]}, expected)
                self.assert_partition(records, result)

    def test_single_group_boundaries(self):
        records = [{"group": "same", "id": i} for i in range(4)]
        for fraction, expected_count in ((0.0, 0), (0.49, 0), (0.5, 4), (0.99, 4), (1, 4)):
            with self.subTest(fraction=fraction):
                result = solve(records, fraction)
                self.assertEqual(len(result["validation"]), expected_count)
                self.assert_partition(records, result)

    def test_duplicate_rows_kept(self):
        shared = {"group": "b", "payload": 17}
        records = [shared, {"group": "a"}, shared, {"group": "c"}, shared]
        result = solve(records, 1 / 3)
        self.assertEqual(len(result["validation"]), 3)
        self.assertTrue(all(row is shared for row in result["validation"]))
        self.assert_partition(records, result)

    def test_invalid_records_container(self):
        for records in (None, (), "abc", {"group": "a"}, iter([])):
            with self.subTest(container=type(records).__name__):
                with self.assertRaises(TypeError):
                    solve(records, 0.5)

    def test_invalid_record_type(self):
        for bad_record in (None, [], "a", 42):
            for fraction in (0, 0.5, 1):
                with self.subTest(record=bad_record, fraction=fraction):
                    with self.assertRaises(TypeError):
                        solve([{"group": "good"}, bad_record], fraction)

    def test_missing_empty_or_non_string_group(self):
        for bad_record in ({}, {"group": ""}, {"group": None}, {"group": 1}, {"group": True}):
            for fraction in (0, 0.5, 1):
                with self.subTest(record=bad_record, fraction=fraction):
                    with self.assertRaises(ValueError):
                        solve([bad_record], fraction)

    def test_invalid_fraction_type(self):
        for fraction in (True, False, "0.5", None, [], complex(0.5, 0)):
            with self.subTest(fraction=fraction):
                with self.assertRaises(TypeError):
                    solve([], fraction)

    def test_invalid_fraction_value(self):
        for fraction in (-1, 2, -0.001, 1.00001, float("nan"), float("inf"), -float("inf")):
            with self.subTest(fraction=fraction):
                with self.assertRaises(ValueError):
                    solve([], fraction)

    def test_invalid_seed_type(self):
        for seed in (True, False, 0.0, "0", None, []):
            with self.subTest(seed=seed):
                with self.assertRaises(TypeError):
                    solve([], 0.5, seed)


if __name__ == "__main__":
    unittest.main()
