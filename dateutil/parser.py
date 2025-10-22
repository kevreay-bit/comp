"""Simplified date parsing helpers to emulate dateutil.parser."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Iterable

__all__ = ["parse"]


_PATTERNS: Iterable[str] = (
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M",
    "%d-%m-%Y %H:%M",
    "%m/%d/%Y %H:%M",
)


def _normalise(text: str) -> str:
    text = text.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return text


def parse(value: str, fuzzy: bool = False) -> datetime:
    if not value:
        raise ValueError("Cannot parse empty date string")
    value = value.strip()

    cleaned = _normalise(value)
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        pass

    for pattern in _PATTERNS:
        try:
            dt = datetime.strptime(cleaned, pattern)
            return dt
        except ValueError:
            continue

    if fuzzy:
        digits = re.search(r"(\d{4}-\d{2}-\d{2})(?:[ T](\d{2}:\d{2}(?::\d{2})?))?", value)
        if digits:
            date_part = digits.group(1)
            time_part = digits.group(2) or "00:00"
            cleaned = _normalise(f"{date_part} {time_part}")
            for pattern in _PATTERNS:
                try:
                    dt = datetime.strptime(cleaned, pattern)
                    return dt
                except ValueError:
                    continue
        alt = re.search(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", value)
        if alt:
            date_part = alt.group(1)
            time_match = re.search(r"(\d{1,2}:\d{2}(?::\d{2})?)", value)
            time_part = time_match.group(1) if time_match else "00:00"
            for pattern in ("%d/%m/%Y %H:%M", "%d-%m-%Y %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%y %H:%M"):
                try:
                    dt = datetime.strptime(f"{date_part} {time_part}", pattern)
                    return dt
                except ValueError:
                    continue
    raise ValueError(f"Could not parse date string: {value}")
