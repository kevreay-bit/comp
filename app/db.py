"""Database utilities for managing raffle data."""

from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Dict, Iterable, Iterator, Tuple

from .config import get_settings

LOGGER = logging.getLogger(__name__)


class Database:
    """Lightweight SQLite database wrapper."""

    def __init__(self, url: str | None = None) -> None:
        settings = get_settings()
        self.url = url or settings.database_url
        if not self.url.startswith("sqlite://"):
            raise ValueError(
                "Only sqlite URLs are supported by the built-in database wrapper."
            )
        self._db_path = self._resolve_sqlite_path(self.url)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        LOGGER.debug("Initializing SQLite database at %s", self._db_path)
        self._initialize()

    @staticmethod
    def _resolve_sqlite_path(url: str) -> Path:
        parsed = urlparse(url)
        if parsed.scheme != "sqlite":
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}")

        if parsed.netloc:
            raise ValueError(
                "SQLite URLs with network locations are not supported: "
                f"{parsed.netloc}"
            )

        if parsed.path.startswith("//"):
            # Four leading slashes in the URL indicates an absolute path
            path = Path(parsed.path[1:])
        else:
            path = Path(parsed.path.lstrip("/"))

        if not path.is_absolute():
            path = Path.cwd() / path
        return path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self._db_path)
        try:
            yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS raffles (
                    source TEXT NOT NULL,
                    raffle_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    price REAL NOT NULL,
                    total_tickets INTEGER NOT NULL,
                    tickets_remaining INTEGER NOT NULL,
                    deadline_utc TEXT NOT NULL,
                    last_updated_utc TEXT NOT NULL,
                    PRIMARY KEY (source, raffle_id)
                )
                """
            )
            conn.commit()

    def upsert_raffles(self, rows: Iterable[Dict[str, object]]) -> None:
        """Perform an UPSERT for the provided raffle rows."""

        with self.connect() as conn:
            conn.executemany(
                """
                INSERT INTO raffles (
                    source,
                    raffle_id,
                    title,
                    price,
                    total_tickets,
                    tickets_remaining,
                    deadline_utc,
                    last_updated_utc
                ) VALUES (
                    :source,
                    :raffle_id,
                    :title,
                    :price,
                    :total_tickets,
                    :tickets_remaining,
                    :deadline_utc,
                    :last_updated_utc
                )
                ON CONFLICT(source, raffle_id) DO UPDATE SET
                    title=excluded.title,
                    price=excluded.price,
                    total_tickets=excluded.total_tickets,
                    tickets_remaining=excluded.tickets_remaining,
                    deadline_utc=excluded.deadline_utc,
                    last_updated_utc=excluded.last_updated_utc
                """,
                list(rows),
            )
            conn.commit()

    def prune_missing(self, present_keys: Iterable[Tuple[str, str]]) -> int:
        """Remove raffles that are no longer returned by the scrapers."""

        keys = list(present_keys)
        if not keys:
            with self.connect() as conn:
                deleted = conn.execute("DELETE FROM raffles").rowcount
                conn.commit()
                return deleted

        placeholders = ",".join(["(?, ?)"] * len(keys))
        flat_params = [item for key in keys for item in key]
        query = (
            "DELETE FROM raffles WHERE (source, raffle_id) NOT IN "
            f"(VALUES {placeholders})"
        )
        with self.connect() as conn:
            cursor = conn.execute(query, flat_params)
            conn.commit()
            return cursor.rowcount

    def fetch_all(self) -> list[dict[str, object]]:
        """Fetch all raffles for debugging or tests."""

        with self.connect() as conn:
            cursor = conn.execute(
                "SELECT source, raffle_id, title, price, total_tickets, "
                "tickets_remaining, deadline_utc, last_updated_utc FROM raffles"
            )
            columns = [description[0] for description in cursor.description]
            rows = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return rows


def serialize_raffle(raffle: "RaffleData") -> Dict[str, object]:
    """Convert a raffle dataclass into a dictionary row."""

    data = asdict(raffle)
    deadline = data.pop("deadline")
    if not isinstance(deadline, datetime):
        raise TypeError("deadline must be a datetime instance in UTC")
    if deadline.tzinfo is None:
        raise ValueError("deadline must be timezone-aware")

    deadline_utc = deadline.astimezone(timezone.utc).replace(microsecond=0)
    data["deadline_utc"] = deadline_utc.isoformat().replace("+00:00", "Z")

    data["last_updated_utc"] = (
        datetime.now(tz=timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )
    return data


# Late import to avoid circular dependency during module import.
from .scrapers import RaffleData  # noqa  E402  pylint: disable=wrong-import-position
