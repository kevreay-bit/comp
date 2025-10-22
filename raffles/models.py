"""Data model used throughout the raffle ingestion pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


def _default_metadata() -> Dict[str, Any]:
    return {}


@dataclass
class RaffleRecord:
    source: str
    raffle_id: str
    name: Optional[str] = None
    total_tickets: Optional[int] = None
    tickets_sold: Optional[int] = None
    min_tickets_for_half_chance: Optional[int] = None
    win_probability_single_ticket: Optional[float] = None
    deadline_ts: Optional[int] = None
    deadline_iso: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=_default_metadata)


__all__ = ["RaffleRecord"]
