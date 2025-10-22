"""Example scraper used for demonstration and testing."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, List

from raffles.models import RaffleRecord
from .base import BaseScraper


class ExampleScraper(BaseScraper):
    source = "example"

    def fetch(self) -> Iterable[RaffleRecord]:
        now = datetime.now(timezone.utc)
        raffles: List[RaffleRecord] = []
        for idx, duration_hours in enumerate((6, 12, 24), start=1):
            total_tickets = 500 * idx
            tickets_sold = 100 * idx
            deadline = now + timedelta(hours=duration_hours)
            record = RaffleRecord(
                source=self.source,
                raffle_id=f"raffle-{idx}",
                name=f"Example raffle #{idx}",
                total_tickets=total_tickets,
                tickets_sold=tickets_sold,
                metadata={
                    "url": f"https://example.com/raffles/{idx}",
                    "ticket_price": 5.0 + idx,
                },
            )
            record.metadata["deadline"] = deadline.isoformat()
            raffles.append(record)
        return raffles


SCRAPER = ExampleScraper()


__all__ = ["ExampleScraper", "SCRAPER"]
