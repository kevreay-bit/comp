"""Simple utility to run all scraper implementations."""

from __future__ import annotations

import logging
from typing import Iterable, Sequence

from .base import BaseScraper
from .pipeline import raffle_queue
from .sites import RaffleSiteAScraper, RaffleSiteBScraper

logger = logging.getLogger(__name__)


def run_scrapers(scrapers: Iterable[BaseScraper]) -> Sequence[BaseScraper]:
    results: list[BaseScraper] = []
    for scraper in scrapers:
        logger.info("Starting %s", scraper.__class__.__name__)
        scraper.run()
        results.append(scraper)
    logger.info("Queue now holds %d entries", raffle_queue.size())
    return results


def default_scrapers() -> list[BaseScraper]:
    return [RaffleSiteAScraper(), RaffleSiteBScraper()]


def main() -> None:  # pragma: no cover - CLI helper
    logging.basicConfig(level=logging.INFO)
    try:
        run_scrapers(default_scrapers())
    except Exception:
        logger.exception("Scraper run failed")
        raise


if __name__ == "__main__":  # pragma: no cover - CLI helper
    main()
