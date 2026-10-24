"""Reference implementation for this newly created AI-assisted sample task."""

from fractions import Fraction
import hashlib
import json
import math


def _validate(records, validation_fraction, seed):
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if isinstance(validation_fraction, bool) or not isinstance(
        validation_fraction, (int, float)
    ):
        raise TypeError("validation_fraction must be an int or float, excluding bool")
    if isinstance(validation_fraction, float) and not math.isfinite(validation_fraction):
        raise ValueError("validation_fraction must be finite")
    if not 0 <= validation_fraction <= 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise TypeError("seed must be an integer, excluding bool")
    for record in records:
        if not isinstance(record, dict):
            raise TypeError("each record must be a dict")
        if not isinstance(record.get("group"), str) or not record["group"]:
            raise ValueError("each record must contain a nonempty string group")


def _validation_count(group_count, validation_fraction):
    # Interpret the public decimal string exactly; avoid binary float and bankers' rounding.
    fraction = Fraction(str(validation_fraction))
    return (
        2 * group_count * fraction.numerator + fraction.denominator
    ) // (2 * fraction.denominator)


def _ranked_groups(records, seed):
    groups = {record["group"] for record in records}

    def rank(group):
        payload = json.dumps(
            [seed, group], ensure_ascii=True, separators=(",", ":")
        ).encode("ascii")
        return hashlib.sha256(payload).digest(), group

    return sorted(groups, key=rank)


def _partition(records, validation_groups):
    result = {"train": [], "validation": []}
    for record in records:
        side = "validation" if record["group"] in validation_groups else "train"
        result[side].append(record)
    return result


def solve(records, validation_fraction, seed=0):
    """Split records by deterministic group rank, preserving each side's row order."""
    _validate(records, validation_fraction, seed)
    groups = _ranked_groups(records, seed)
    count = _validation_count(len(groups), validation_fraction)
    return _partition(records, set(groups[:count]))
