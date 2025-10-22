"""Data models shared across scraper implementations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class RaffleEntry:
    """Normalized record describing a raffle opportunity."""

    title: str
    prize: str
    ticket_count: Optional[int]
    price: Optional[float]
    deadline: Optional[datetime]
    url: str

    def as_dict(self) -> dict[str, object]:
        """Return the dataclass as a JSON-serialisable dictionary."""

        return {
            "title": self.title,
            "prize": self.prize,
            "ticket_count": self.ticket_count,
            "price": self.price,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "url": self.url,
        }
