"""Scheduler setup for periodic raffle ingestion."""

from __future__ import annotations

import logging
import time
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import get_settings
from .ingest import IngestionError, ingest_all

LOGGER = logging.getLogger(__name__)


def _run_ingestion_job() -> None:
    try:
        result = ingest_all()
        LOGGER.info(
            "Ingestion job succeeded at %s: %s records ingested, %s deleted",
            result["timestamp"],
            result["ingested"],
            result["deleted"],
        )
    except IngestionError as exc:
        LOGGER.warning("Ingestion completed with scraper failures: %s", exc)
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Ingestion job crashed")


def start_scheduler() -> BackgroundScheduler:
    """Start a background scheduler that periodically runs ingestion."""

    settings = get_settings()
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _run_ingestion_job,
        trigger=IntervalTrigger(
            seconds=int(settings.ingestion_interval.total_seconds())
        ),
        id="raffle-ingestion",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    LOGGER.info(
        "Scheduler started at %s with interval %s", datetime.utcnow().isoformat(), settings.ingestion_interval
    )
    return scheduler


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    scheduler = start_scheduler()
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        LOGGER.info("Stopping scheduler")
        scheduler.shutdown(wait=False)
