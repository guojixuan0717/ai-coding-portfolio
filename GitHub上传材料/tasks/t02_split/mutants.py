"""Deliberately incorrect implementations used to check test discrimination.

Validation and unaffected plumbing reuse the reference; each mutant introduces
one realistic algorithm error. These are evaluation fixtures, not submissions.
"""

import random

from .reference import (
    _partition,
    _ranked_groups,
    _validation_count,
    solve as _reference,
)


def mutant_row_split(records, validation_fraction, seed=0):
    """BUG: samples rows, so examples from one group can leak across the split."""
    _reference(records, validation_fraction, seed)
    count = _validation_count(len(records), validation_fraction)
    chosen = set(random.Random(seed).sample(range(len(records)), count))
    return {
        "train": [record for i, record in enumerate(records) if i not in chosen],
        "validation": [record for i, record in enumerate(records) if i in chosen],
    }


def mutant_bankers_rounding(records, validation_fraction, seed=0):
    """BUG: round() rounds exact .5 ties to even instead of upward."""
    _reference(records, validation_fraction, seed)
    groups = _ranked_groups(records, seed)
    count = round(len(groups) * validation_fraction)
    return _partition(records, set(groups[:count]))


def mutant_first_seen_groups(records, validation_fraction, seed=0):
    """BUG: first appearance replaces the specified stable hash ordering."""
    _reference(records, validation_fraction, seed)
    groups = list(dict.fromkeys(record["group"] for record in records))
    count = _validation_count(len(groups), validation_fraction)
    return _partition(records, set(groups[:count]))
