"""Ingestion pipeline that runs all scrapers and updates the raffles store."""
from __future__ import annotations

import argparse
import json
import logging
import math
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Iterable, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from raffles.db import init_db, prune_stale, upsert_raffles
from raffles.models import RaffleRecord
from raffles.settings import get_database_url, get_prune_hours
from scrapers import discover

LOGGER = logging.getLogger(__name__)


def _parse_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        return value
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.fromisoformat(text)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"Unsupported datetime format: {value}") from exc


def _ensure_deadline(record: RaffleRecord) -> None:
    deadline_value = None
    if record.deadline_iso:
        deadline_value = record.deadline_iso
    elif record.metadata.get("deadline"):
        deadline_value = record.metadata["deadline"]
    if deadline_value is None:
        return
    try:
        deadline_dt = _parse_datetime(deadline_value)
    except ValueError as exc:  # pragma: no cover - defensive
        LOGGER.warning("Unable to parse deadline '%s' for %s:%s: %s", deadline_value, record.source, record.raffle_id, exc)
        return
    if deadline_dt.tzinfo is None:
        deadline_dt = deadline_dt.replace(tzinfo=timezone.utc)
    else:
        deadline_dt = deadline_dt.astimezone(timezone.utc)
    record.deadline_iso = deadline_dt.isoformat()
    record.deadline_ts = int(deadline_dt.timestamp())


def _compute_odds(record: RaffleRecord) -> None:
    total = record.total_tickets
    if not total or total <= 0:
        record.win_probability_single_ticket = None
        record.min_tickets_for_half_chance = None
        return
    record.win_probability_single_ticket = 1.0 / total
    probability_of_not_winning = 1.0 - record.win_probability_single_ticket
    if probability_of_not_winning <= 0:
        record.min_tickets_for_half_chance = 1
        return
    # Solve (1 - p)**n <= 0.5  -> n >= log(0.5)/log(1 - p)
    min_tickets = math.log(0.5) / math.log(probability_of_not_winning)
    record.min_tickets_for_half_chance = max(1, math.ceil(min_tickets))


def enrich_records(records: Iterable[RaffleRecord]) -> List[RaffleRecord]:
    enriched: List[RaffleRecord] = []
    for record in records:
        _ensure_deadline(record)
        _compute_odds(record)
        enriched.append(record)
    return enriched


def run_ingestion(database_url: str | None = None, prune_hours: float | None = None) -> dict:
    """Run the ingestion pipeline and return summary statistics."""

    init_db(database_url)
    scrapers = discover()
    LOGGER.info("Discovered %d scrapers", len(scrapers))

    all_records: List[RaffleRecord] = []
    for scraper in scrapers:
        try:
            collected = scraper.collect()
        except Exception:  # pragma: no cover - defensive logging
            LOGGER.exception("Scraper %s failed", scraper)
            continue
        LOGGER.info("Scraper %s returned %d raffles", scraper.__class__.__name__, len(collected))
        all_records.extend(enrich_records(collected))

    affected = upsert_raffles(all_records, database_url)

    retention_hours = prune_hours if prune_hours is not None else get_prune_hours()
    prune_before = datetime.now(timezone.utc) - timedelta(hours=retention_hours)
    pruned = prune_stale(prune_before, database_url)

    LOGGER.info("Upserted %d rows, pruned %d stale raffles", affected, pruned)
    return {
        "scrapers": len(scrapers),
        "processed": len(all_records),
        "upserted": affected,
        "pruned": pruned,
        "retention_hours": retention_hours,
    }


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run raffle ingestion pipeline")
    parser.add_argument("--database-url", dest="database_url", default=get_database_url())
    parser.add_argument("--prune-hours", dest="prune_hours", type=float, default=get_prune_hours())
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    LOGGER.debug("Arguments: %s", args)

    summary = run_ingestion(database_url=args.database_url, prune_hours=args.prune_hours)
    LOGGER.info("Ingestion summary: %s", json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
