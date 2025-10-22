from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class RaffleEntry:
    """Normalized raffle information produced by scrapers."""

    source: str
    raffle_id: str
    title: str
    prize: str
    total_tickets: Optional[int]
    tickets_sold: Optional[int]
    ticket_price: Optional[float]
    deadline: Optional[datetime]
    url: str

    def odds(self) -> Optional[float]:
        """Return the probability of winning (lower is better) if known."""

        if self.total_tickets and self.total_tickets > 0 and self.tickets_sold is not None:
            return self.tickets_sold / float(self.total_tickets)
        return None
