from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

import uvicorn

from .api import create_app
from .database import Database
from .ingestion import RaffleScraper, run_ingestion
from .models import RaffleEntry
from .repository import RaffleRepository
from .scheduler import IngestionScheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

DEFAULT_DB_PATH = Path("data/raffles.db")


class DummyScraper:
    """Simple scraper stub so the demo API returns data."""

    name = "demo"

    def fetch(self) -> Iterable[RaffleEntry]:
        return [
            RaffleEntry(
                source=self.name,
                raffle_id="example",
                title="Demo Prize Pack",
                prize="Bundle of popular gadgets",
                total_tickets=500,
                tickets_sold=125,
                ticket_price=2.5,
                deadline=None,
                url="https://example.com/raffles/demo",
            )
        ]


def build_repository(db_path: Path = DEFAULT_DB_PATH) -> RaffleRepository:
    database = Database(db_path)
    return RaffleRepository(database)


def build_scrapers() -> list[RaffleScraper]:
    return [DummyScraper()]


def configure_scheduler(app, repository: RaffleRepository, scrapers: list[RaffleScraper], interval_minutes: int = 15) -> IngestionScheduler:
    scheduler = IngestionScheduler(scrapers, repository, interval_minutes=interval_minutes)

    @app.on_event("startup")
    async def _startup() -> None:  # pragma: no cover - FastAPI lifecycle hook
        run_ingestion(scrapers, repository)
        scheduler.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:  # pragma: no cover - FastAPI lifecycle hook
        scheduler.shutdown()

    return scheduler


def create_service(db_path: Path = DEFAULT_DB_PATH) -> tuple[uvicorn.Config, IngestionScheduler]:
    repository = build_repository(db_path)
    scrapers = build_scrapers()
    app = create_app(repository)
    scheduler = configure_scheduler(app, repository, scrapers)
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, reload=False)
    return config, scheduler


def run() -> None:
    config, scheduler = create_service()
    server = uvicorn.Server(config)

    try:
        server.run()
    finally:
        scheduler.shutdown()


_repository = build_repository(DEFAULT_DB_PATH)
_scrapers = build_scrapers()
app = create_app(_repository)
_scheduler = configure_scheduler(app, _repository, _scrapers)


if __name__ == "__main__":
    run()
