"""Deliberately incorrect sample candidates, used to check test sensitivity.

These are educational counterexamples, not implementations for submission.
"""

from __future__ import annotations

import unicodedata
from typing import Any

try:
    from .reference import solve as _reference
except ImportError:  # Allow unittest discovery directly in this directory.
    from reference import solve as _reference


def _key(record, fields, normalize, *, lowercase=False):
    values = []
    for field in fields:
        value = record[field]
        if normalize:
            value = unicodedata.normalize("NFKC", value)
            value = (value.lower() if lowercase else value.casefold()).strip()
        values.append(value)
    return tuple(values)


def mutant_last_wins(
    records: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...] = ("prompt", "response"),
    normalize: bool = True,
) -> list[dict[str, Any]]:
    """Bug: overwriting a dict entry keeps the last duplicate's metadata."""
    _reference(records, key_fields=key_fields, normalize=normalize)
    unique = {}
    for record in records:
        unique[_key(record, key_fields, normalize)] = record.copy()
    return list(unique.values())


def mutant_lowercase(
    records: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...] = ("prompt", "response"),
    normalize: bool = True,
) -> list[dict[str, Any]]:
    """Bug: lower() does not implement Unicode casefold(), e.g. German ß."""
    _reference(records, key_fields=key_fields, normalize=normalize)
    seen = set()
    result = []
    for record in records:
        key = _key(record, key_fields, normalize, lowercase=True)
        if key not in seen:
            seen.add(key)
            result.append(record.copy())
    return result


def mutant_first_field(
    records: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...] = ("prompt", "response"),
    normalize: bool = True,
) -> list[dict[str, Any]]:
    """Bug: deduplication silently ignores every field after the first."""
    _reference(records, key_fields=key_fields, normalize=normalize)
    seen = set()
    result = []
    for record in records:
        key = _key(record, key_fields[:1], normalize)
        if key not in seen:
            seen.add(key)
            result.append(record.copy())
    return result
