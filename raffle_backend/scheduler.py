from __future__ import annotations

import logging
from datetime import datetime
from typing import Iterable

from apscheduler.schedulers.background import BackgroundScheduler

from .ingestion import RaffleScraper, run_ingestion
from .repository import RaffleRepository

logger = logging.getLogger(__name__)


class IngestionScheduler:
    """Wraps APScheduler to refresh raffle data on an interval."""

    def __init__(
        self,
        scrapers: Iterable[RaffleScraper],
        repository: RaffleRepository,
        *,
        interval_minutes: int = 15,
    ) -> None:
        self.scrapers = list(scrapers)
        self.repository = repository
        self.scheduler = BackgroundScheduler()
        self.interval_minutes = interval_minutes
        self.job = None

    def start(self) -> None:
        if self.job is None:
            self.job = self.scheduler.add_job(
                self._run,
                "interval",
                minutes=self.interval_minutes,
                next_run_time=datetime.now(self.scheduler.timezone),
            )
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Started ingestion scheduler with %d minute interval", self.interval_minutes)

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Stopped ingestion scheduler")

    def _run(self) -> None:
        count = run_ingestion(self.scrapers, self.repository)
        logger.info("Ingestion cycle processed %d raffles", count)
