"""Candidate starter for an AI-assisted task; all data is synthetic."""

from __future__ import annotations

from typing import Any


def solve(
    records: list[dict[str, Any]],
    *,
    key_fields: tuple[str, ...] = ("prompt", "response"),
    normalize: bool = True,
) -> list[dict[str, Any]]:
    raise NotImplementedError("Implement the contract in SPEC.md")
