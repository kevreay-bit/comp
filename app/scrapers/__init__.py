"""Scraper interfaces and simple demo implementations."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable, Protocol

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RaffleData:
    """Normalized raffle representation produced by scrapers."""

    source: str
    raffle_id: str
    title: str
    price: float
    total_tickets: int
    tickets_remaining: int
    deadline: datetime


class RaffleScraper(Protocol):
    """Protocol for raffle scrapers."""

    source: str

    def run(self) -> Iterable[RaffleData]:
        """Return the list of raffles discovered by this scraper."""


class StaticScraper:
    """A simple scraper implementation returning hard-coded data."""

    source = "static"

    def run(self) -> Iterable[RaffleData]:
        now = datetime.now(tz=timezone.utc)
        LOGGER.debug("StaticScraper generating sample data at %s", now.isoformat())
        return [
            RaffleData(
                source=self.source,
                raffle_id="demo-001",
                title="Demo Console Giveaway",
                price=5.0,
                total_tickets=100,
                tickets_remaining=42,
                deadline=now.replace(hour=(now.hour + 6) % 24),
            ),
            RaffleData(
                source=self.source,
                raffle_id="demo-002",
                title="Guitar Raffle",
                price=10.0,
                total_tickets=200,
                tickets_remaining=180,
                deadline=now.replace(day=min(now.day + 1, 28)),
            ),
        ]


def get_scrapers() -> list[RaffleScraper]:
    """Return the list of registered scrapers."""

    return [StaticScraper()]
