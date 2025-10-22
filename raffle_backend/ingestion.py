from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable, Protocol

from .models import RaffleEntry
from .repository import RaffleRepository


class RaffleScraper(Protocol):
    """Protocol for scraper implementations used by the ingestion pipeline."""

    name: str

    def fetch(self) -> Iterable[RaffleEntry]:
        ...


def run_ingestion(
    scrapers: Iterable[RaffleScraper],
    repository: RaffleRepository,
    *,
    prune_after_hours: int = 24,
) -> int:
    """Run all scrapers and upsert their entries into the repository.

    Returns the total number of raffle entries processed.
    """

    all_entries: list[RaffleEntry] = []
    for scraper in scrapers:
        entries = list(scraper.fetch())
        all_entries.extend(entries)

    prune_before = datetime.now(timezone.utc) - timedelta(hours=prune_after_hours)
    repository.upsert_entries(all_entries, prune_before=prune_before)
    return len(all_entries)
