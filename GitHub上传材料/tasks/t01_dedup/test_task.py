"""Independent contract tests for an AI-assisted, synthetic example task."""

from __future__ import annotations

import copy
import importlib
import os
import random
import unittest


def _load_solve():
    implementation = os.environ.get("AI_PORTFOLIO_IMPL", "reference")
    if implementation in {"reference", "starter"}:
        module_name = implementation
        function_name = "solve"
    elif implementation in {
        "mutant_last_wins", "mutant_lowercase", "mutant_first_field"
    }:
        module_name = "mutants"
        function_name = implementation
    else:
        raise ValueError(f"Unknown AI_PORTFOLIO_IMPL: {implementation!r}")
    module = importlib.import_module(
        f".{module_name}" if __package__ else module_name,
        package=__package__ or None,
    )
    return getattr(module, function_name)


solve = _load_solve()


class DedupTaskTests(unittest.TestCase):
    def test_empty_input(self):
        records = []
        result = solve(records)
        self.assertEqual(result, [])
        self.assertIsNot(result, records)

    def test_first_occurrence_metadata(self):
        records = [
            {"prompt": "p", "response": "r", "source": "first"},
            {"prompt": "p", "response": "r", "source": "second"},
        ]
        self.assertEqual(solve(records), [records[0]])

    def test_preserves_order_with_nonadjacent_duplicates(self):
        records = [
            {"prompt": "z", "response": "1"},
            {"prompt": "a", "response": "2"},
            {"prompt": "z", "response": "1"},
            {"prompt": "m", "response": "3"},
        ]
        self.assertEqual(solve(records), [records[0], records[1], records[3]])

    def test_all_key_fields_participate(self):
        records = [
            {"prompt": "same", "response": "A"},
            {"prompt": "same", "response": "B"},
            {"prompt": "other", "response": "A"},
        ]
        self.assertEqual(solve(records), records)

    def test_nfkc_normalization(self):
        records = [
            {"prompt": "ＡＢＣ", "response": "①"},
            {"prompt": "ABC", "response": "1"},
            {"prompt": "e\u0301", "response": "x"},
            {"prompt": "é", "response": "x"},
        ]
        self.assertEqual(solve(records), [records[0], records[2]])

    def test_unicode_casefold(self):
        records = [
            {"prompt": "Straße", "response": "Σ"},
            {"prompt": "STRASSE", "response": "ς"},
        ]
        self.assertEqual(solve(records), [records[0]])

    def test_strip_and_internal_whitespace(self):
        records = [
            {"prompt": "\t hello \n", "response": "\u3000ok\u3000"},
            {"prompt": "hello", "response": "ok"},
            {"prompt": "he llo", "response": "ok"},
            {"prompt": "he  llo", "response": "ok"},
        ]
        self.assertEqual(solve(records), [records[0], records[2], records[3]])

    def test_normalization_can_be_disabled(self):
        records = [
            {"prompt": "Ａ", "response": "R"},
            {"prompt": "A", "response": "R"},
            {"prompt": "a", "response": "R"},
            {"prompt": " A ", "response": "R"},
            {"prompt": "Ａ", "response": "R"},
        ]
        self.assertEqual(solve(records, normalize=False), records[:4])

    def test_custom_key_fields(self):
        records = [
            {"language": "ZH", "question": "q", "answer": "a", "id": 1},
            {"language": "zh", "question": "q", "answer": "b", "id": 2},
            {"language": "en", "question": "q", "answer": "c", "id": 3},
        ]
        self.assertEqual(
            solve(records, key_fields=("language", "question")),
            [records[0], records[2]],
        )
        self.assertEqual(solve(records, key_fields=("answer",)), records)

    def test_does_not_mutate_input(self):
        records = [
            {"prompt": " Ａ ", "response": " R ", "meta": {"tags": ["x"]}},
            {"prompt": "a", "response": "r", "meta": {"tags": ["y"]}},
        ]
        original = copy.deepcopy(records)
        solve(records)
        self.assertEqual(records, original)

    def test_returns_shallow_dictionary_copies(self):
        nested = {"labels": ["synthetic"]}
        records = [{"prompt": "p", "response": "r", "meta": nested}]
        result = solve(records)
        self.assertIsNot(result[0], records[0])
        self.assertIs(result[0]["meta"], nested)
        result[0]["prompt"] = "changed"
        self.assertEqual(records[0]["prompt"], "p")

    def test_key_boundaries_and_empty_values(self):
        records = [
            {"prompt": "ab", "response": "c"},
            {"prompt": "a", "response": "bc"},
            {"prompt": "", "response": "x"},
            {"prompt": " ", "response": "x"},
            {"prompt": "x", "response": ""},
        ]
        self.assertEqual(solve(records), [records[0], records[1], records[2], records[4]])

    def test_invalid_records_container(self):
        for invalid in (None, {}, (), "text", 7, True):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                solve(invalid)

    def test_invalid_record_shapes_and_keys(self):
        for invalid in (None, [], "text", 7, {1: "x", "prompt": "p", "response": "r"}):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                solve([{"prompt": "p", "response": "r"}, invalid])

    def test_missing_required_fields(self):
        for invalid in ({}, {"prompt": "p"}, {"response": "r"}):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                solve([{"prompt": "p", "response": "r"}, invalid])
        with self.assertRaises(ValueError):
            solve([{"id": "a"}], key_fields=("id", "text"))

    def test_required_values_must_be_strings(self):
        for value in (None, 0, False, [], {}, b"bytes"):
            for field in ("prompt", "response"):
                record = {"prompt": "p", "response": "r", field: value}
                with self.subTest(value=value, field=field), self.assertRaises(TypeError):
                    solve([{"prompt": "p", "response": "r"}, record])

    def test_invalid_key_fields_container(self):
        for invalid in (None, [], ["prompt"], "prompt", {"prompt"}, 1):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                solve([], key_fields=invalid)

    def test_invalid_key_fields_content(self):
        for invalid in ((), ("",), ("prompt", "prompt")):
            with self.subTest(value=invalid), self.assertRaises(ValueError):
                solve([], key_fields=invalid)
        for invalid in ((1,), (None,), ("prompt", False)):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                solve([], key_fields=invalid)

    def test_normalize_requires_actual_bool(self):
        for invalid in (None, 0, 1, "true", [], {}):
            with self.subTest(value=invalid), self.assertRaises(TypeError):
                solve([], normalize=invalid)

    def test_seeded_ascii_first_occurrence_oracle(self):
        # This oracle uses integer labels supplied before string rendering.
        # It does not duplicate Unicode canonicalization or call reference.py.
        rng = random.Random(20261024)
        records = []
        expected = []
        seen = set()
        for index in range(150):
            left, right = rng.randrange(8), rng.randrange(6)
            record = {
                "prompt": f"  ITEM{left} " if index % 2 else f"item{left}",
                "response": f" RESULT{right}\n" if index % 3 else f"result{right}",
                "sequence": index,
            }
            records.append(record)
            label = (left, right)
            if label not in seen:
                seen.add(label)
                expected.append(record)
        self.assertEqual(solve(records), expected)


if __name__ == "__main__":
    unittest.main()
