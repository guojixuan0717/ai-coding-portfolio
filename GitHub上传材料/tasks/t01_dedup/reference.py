"""Reference implementation for an AI-assisted, synthetic portfolio task."""

from __future__ import annotations

import unicodedata
from typing import Any


def solve(
    records: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...] = ("prompt", "response"),
    normalize: bool = True,
) -> list[dict[str, Any]]:
    """Keep the first record for each comparison key without changing input.

    Returned dictionaries are shallow copies. Nested metadata is shared, but
    this function does not write to either records or nested metadata.
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list")
    if not isinstance(key_fields, tuple):
        raise TypeError("key_fields must be a tuple")
    if not key_fields:
        raise ValueError("key_fields must not be empty")
    for field in key_fields:
        if not isinstance(field, str):
            raise TypeError("every key field must be a string")
        if not field:
            raise ValueError("key fields must not be empty strings")
    if len(set(key_fields)) != len(key_fields):
        raise ValueError("key fields must be unique")
    if type(normalize) is not bool:
        raise TypeError("normalize must be a bool")

    seen: set[tuple[str, ...]] = set()
    result: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise TypeError(f"record {index} must be a dict")
        if any(not isinstance(name, str) for name in record):
            raise TypeError(f"record {index} keys must be strings")
        key_parts = []
        for field in key_fields:
            if field not in record:
                raise ValueError(f"record {index} is missing {field!r}")
            value = record[field]
            if not isinstance(value, str):
                raise TypeError(f"record {index} field {field!r} must be a string")
            if normalize:
                value = unicodedata.normalize("NFKC", value).casefold().strip()
            key_parts.append(value)
        key = tuple(key_parts)
        if key not in seen:
            seen.add(key)
            result.append(record.copy())
    return result
