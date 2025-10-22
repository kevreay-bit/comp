from __future__ import annotations

import argparse
import logging
from pathlib import Path

from raffle_backend.ingestion import run_ingestion
from raffle_backend.main import build_repository, build_scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the raffle ingestion pipeline once")
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("data/raffles.db"),
        help="Path to the SQLite database file",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository = build_repository(args.database)
    scrapers = build_scrapers()
    count = run_ingestion(scrapers, repository)
    logging.info("Ingestion finished with %d entries", count)


if __name__ == "__main__":
    main()
