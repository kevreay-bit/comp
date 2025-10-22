"""CLI entrypoint to run all raffle scrapers and persist results."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

# Ensure the repository root is importable when executing the script directly.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db import Database
from app.ingest import IngestionError, ingest_all

LOGGER = logging.getLogger("raffles.ingestion")


def configure_logging(verbose: bool = False) -> None:
    """Configure root logging handlers."""

    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable debug logging output."
    )
    parser.add_argument(
        "--database-url",
        help="Optional database URL override. Defaults to RAFFLES_DATABASE_URL.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    database = Database(url=args.database_url) if args.database_url else None

    try:
        result = ingest_all(database=database)
    except IngestionError as exc:
        LOGGER.error("Ingestion completed with failures: %s", exc)
        return 1
    except Exception:  # pylint: disable=broad-except
        LOGGER.exception("Unexpected error while running ingestion")
        return 2

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
