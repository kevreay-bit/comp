"""Database helpers for managing raffle records."""
from __future__ import annotations

import contextlib
import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Iterator, Optional

from .models import RaffleRecord
from .settings import get_database_url

SQLITE_PREFIX = "sqlite:///"


def _resolve_sqlite_path(database_url: str) -> Path:
    if not database_url.startswith(SQLITE_PREFIX):
        raise ValueError("Only sqlite URLs are supported, e.g. sqlite:///path/to/db.sqlite")
    return Path(database_url[len(SQLITE_PREFIX) :])


def get_connection(database_url: Optional[str] = None) -> sqlite3.Connection:
    """Create a SQLite connection, initialising the database if required."""

    url = database_url or get_database_url()
    path = _resolve_sqlite_path(url)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(database_url: Optional[str] = None) -> None:
    """Initialise the database schema if it does not already exist."""

    with contextlib.closing(get_connection(database_url)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS raffles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                raffle_id TEXT NOT NULL,
                name TEXT,
                total_tickets INTEGER,
                tickets_sold INTEGER,
                min_tickets_for_half_chance INTEGER,
                win_probability_single_ticket REAL,
                deadline_ts INTEGER,
                deadline_iso TEXT,
                metadata_json TEXT,
                last_seen TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
                UNIQUE (source, raffle_id)
            )
            """
        )
        conn.commit()


def upsert_raffles(records: Iterable[RaffleRecord], database_url: Optional[str] = None) -> int:
    """Insert or update raffle records in the database.

    Returns the number of affected rows.
    """

    url = database_url or get_database_url()
    now = datetime.now(timezone.utc).isoformat()
    with contextlib.closing(get_connection(url)) as conn:
        cursor = conn.cursor()
        affected = 0
        for record in records:
            payload = asdict(record)
            payload.setdefault("metadata", {})
            metadata_json = json.dumps(payload.pop("metadata"), sort_keys=True)
            cursor.execute(
                """
                INSERT INTO raffles (
                    source,
                    raffle_id,
                    name,
                    total_tickets,
                    tickets_sold,
                    min_tickets_for_half_chance,
                    win_probability_single_ticket,
                    deadline_ts,
                    deadline_iso,
                    metadata_json,
                    last_seen,
                    updated_at
                ) VALUES (
                    :source,
                    :raffle_id,
                    :name,
                    :total_tickets,
                    :tickets_sold,
                    :min_tickets_for_half_chance,
                    :win_probability_single_ticket,
                    :deadline_ts,
                    :deadline_iso,
                    :metadata_json,
                    :last_seen,
                    :updated_at
                )
                ON CONFLICT(source, raffle_id) DO UPDATE SET
                    name = excluded.name,
                    total_tickets = excluded.total_tickets,
                    tickets_sold = excluded.tickets_sold,
                    min_tickets_for_half_chance = excluded.min_tickets_for_half_chance,
                    win_probability_single_ticket = excluded.win_probability_single_ticket,
                    deadline_ts = excluded.deadline_ts,
                    deadline_iso = excluded.deadline_iso,
                    metadata_json = excluded.metadata_json,
                    last_seen = excluded.last_seen,
                    updated_at = excluded.updated_at
                """,
                {
                    **payload,
                    "metadata_json": metadata_json,
                    "last_seen": now,
                    "updated_at": now,
                },
            )
            affected += cursor.rowcount
        conn.commit()
        return affected


def prune_stale(last_seen_before: datetime, database_url: Optional[str] = None) -> int:
    """Delete raffles that have not been seen since the supplied timestamp."""

    cutoff_iso = last_seen_before.isoformat()
    url = database_url or get_database_url()
    with contextlib.closing(get_connection(url)) as conn:
        cursor = conn.execute(
            "DELETE FROM raffles WHERE last_seen < ?",
            (cutoff_iso,),
        )
        conn.commit()
        return cursor.rowcount


def fetch_all(database_url: Optional[str] = None) -> Iterator[Dict[str, object]]:
    """Return all raffle rows as dictionaries."""

    url = database_url or get_database_url()
    with contextlib.closing(get_connection(url)) as conn:
        for row in conn.execute(
            "SELECT source, raffle_id, name, total_tickets, tickets_sold, "
            "min_tickets_for_half_chance, win_probability_single_ticket, "
            "deadline_ts, deadline_iso, metadata_json, last_seen FROM raffles"
        ):
            data = dict(row)
            metadata = data.get("metadata_json")
            if metadata:
                data["metadata"] = json.loads(metadata)
            else:
                data["metadata"] = {}
            data.pop("metadata_json", None)
            yield data


__all__ = [
    "get_connection",
    "init_db",
    "upsert_raffles",
    "prune_stale",
    "fetch_all",
    "get_database_url",
]
