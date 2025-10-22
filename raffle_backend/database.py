from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS raffles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,
    raffle_id TEXT NOT NULL,
    title TEXT NOT NULL,
    prize TEXT NOT NULL,
    total_tickets INTEGER,
    tickets_sold INTEGER,
    ticket_price REAL,
    deadline TEXT,
    url TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    UNIQUE(source, raffle_id)
);

CREATE INDEX IF NOT EXISTS idx_raffles_deadline ON raffles(deadline);
CREATE INDEX IF NOT EXISTS idx_raffles_odds ON raffles(tickets_sold, total_tickets);
"""


class Database:
    """SQLite helper that ensures the schema exists."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        if self.path.parent and not self.path.parent.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialise(self) -> None:
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    def executemany(self, query: str, rows: Iterable[tuple]) -> None:
        with self.connect() as conn:
            conn.executemany(query, list(rows))
            conn.commit()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self.connect()
        cur = conn.execute(query, params)
        conn.commit()
        conn.close()
        return cur
