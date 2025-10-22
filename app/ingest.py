"""Ingestion workflow for aggregating raffle data from all scrapers."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List

from .db import Database, serialize_raffle
from .scrapers import RaffleData, get_scrapers

LOGGER = logging.getLogger(__name__)


class IngestionError(Exception):
    """Raised when one or more scrapers fail during ingestion."""


def _normalize_raffle(raffle: RaffleData) -> RaffleData:
    """Ensure the raffle dataclass contains UTC deadline information."""

    if raffle.deadline.tzinfo is None:
        raise ValueError(
            f"Scraper {raffle.source} returned a naive datetime for raffle {raffle.raffle_id}"
        )
    deadline_utc = raffle.deadline.astimezone(timezone.utc)
    return RaffleData(
        source=raffle.source,
        raffle_id=raffle.raffle_id,
        title=raffle.title,
        price=float(raffle.price),
        total_tickets=int(raffle.total_tickets),
        tickets_remaining=int(raffle.tickets_remaining),
        deadline=deadline_utc.replace(microsecond=0),
    )


def ingest_all(database: Database | None = None) -> dict[str, object]:
    """Run every scraper, persist results, and prune stale records."""

    database = database or Database()
    scrapers = get_scrapers()
    normalized: List[RaffleData] = []
    failures: List[tuple[str, Exception]] = []

    for scraper in scrapers:
        try:
            LOGGER.info("Running scraper: %s", scraper.source)
            for raffle in scraper.run():
                normalized.append(_normalize_raffle(raffle))
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception("Scraper %s failed", scraper.source)
            failures.append((scraper.source, exc))

    serialized_rows = [serialize_raffle(item) for item in normalized]
    database.upsert_raffles(serialized_rows)

    deleted_rows = 0
    if not failures:
        deleted_rows = database.prune_missing(
            [(item.source, item.raffle_id) for item in normalized]
        )
    else:
        LOGGER.warning(
            "Skipping prune step due to scraper failures: %s",
            ", ".join(src for src, _ in failures),
        )

    result = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "scrapers": [scraper.source for scraper in scrapers],
        "ingested": len(normalized),
        "deleted": deleted_rows,
        "failed": [source for source, _ in failures],
    }

    if failures:
        raise IngestionError(
            f"One or more scrapers failed: {', '.join(src for src, _ in failures)}"
        )

    LOGGER.info(
        "Ingestion run complete: %s ingested, %s deleted",
        result["ingested"],
        result["deleted"],
    )

    return result
