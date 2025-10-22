"""Utility helpers shared across scrapers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from dateutil import parser as date_parser


@dataclass(slots=True)
class NormalizedTicketMetrics:
    sold: Optional[int]
    remaining: Optional[int]
    total: Optional[int]
    sold_ratio: Optional[float]


def parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(re.sub(r"[^0-9]", "", value))
    except ValueError:
        return None


def parse_price(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    cleaned = re.sub(r"[^0-9.,]", "", value)
    cleaned = cleaned.replace(",", "")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_countdown_text(value: Optional[str], *, now: Optional[datetime] = None) -> Optional[str]:
    """Parse a countdown or deadline text into an ISO 8601 timestamp."""

    if value is None:
        return None
    value = value.strip()
    if not value:
        return None

    try:
        parsed = date_parser.parse(value, fuzzy=True)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.isoformat()
    except (ValueError, OverflowError):
        pass

    now = now or datetime.now(timezone.utc)
    pattern = re.compile(
        r"(?:(?P<days>\d+)\s*(?:day|d)\w*)?\s*"
        r"(?:(?P<hours>\d+)\s*(?:hour|h)\w*)?\s*"
        r"(?:(?P<minutes>\d+)\s*(?:minute|min|m)\w*)?\s*"
        r"(?:(?P<seconds>\d+)\s*(?:second|sec|s)\w*)?",
        re.IGNORECASE,
    )
    for match in pattern.finditer(value):
        if not any(match.groupdict().values()):
            continue
        delta = timedelta(
            days=int(match.group("days") or 0),
            hours=int(match.group("hours") or 0),
            minutes=int(match.group("minutes") or 0),
            seconds=int(match.group("seconds") or 0),
        )
        return (now + delta).isoformat()

    return None


def normalize_ticket_metrics(
    *, total: Optional[int], sold: Optional[int], remaining: Optional[int]
) -> NormalizedTicketMetrics:
    """Return consistent ticket metrics, inferring missing values where possible."""

    if total is None:
        if sold is not None and remaining is not None:
            total = sold + remaining
    if sold is None and total is not None and remaining is not None:
        sold = max(total - remaining, 0)
    if remaining is None and total is not None and sold is not None:
        remaining = max(total - sold, 0)

    sold_ratio: Optional[float] = None
    if sold is not None and total:
        sold_ratio = min(max(sold / total, 0.0), 1.0)

    return NormalizedTicketMetrics(sold=sold, remaining=remaining, total=total, sold_ratio=sold_ratio)


__all__ = [
    "NormalizedTicketMetrics",
    "normalize_ticket_metrics",
    "parse_countdown_text",
    "parse_int",
    "parse_price",
]
