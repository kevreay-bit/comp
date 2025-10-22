from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, List, Optional

from dateutil import parser

from .database import Database
from .models import RaffleEntry


class RaffleRepository:
    """Persistence helper for raffle entries."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.database.initialise()

    def upsert_entries(self, entries: Iterable[RaffleEntry], *, prune_before: Optional[datetime] = None) -> None:
        now = datetime.now(timezone.utc).isoformat()
        rows = []
        for entry in entries:
            rows.append(
                (
                    entry.source,
                    entry.raffle_id,
                    entry.title,
                    entry.prize,
                    entry.total_tickets,
                    entry.tickets_sold,
                    entry.ticket_price,
                    entry.deadline.isoformat() if entry.deadline else None,
                    entry.url,
                    now,
                )
            )

        if rows:
            self.database.executemany(
                """
                INSERT INTO raffles (source, raffle_id, title, prize, total_tickets, tickets_sold, ticket_price, deadline, url, last_seen)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, raffle_id) DO UPDATE SET
                    title=excluded.title,
                    prize=excluded.prize,
                    total_tickets=excluded.total_tickets,
                    tickets_sold=excluded.tickets_sold,
                    ticket_price=excluded.ticket_price,
                    deadline=excluded.deadline,
                    url=excluded.url,
                    last_seen=excluded.last_seen
                """,
                rows,
            )

        if prune_before:
            self.database.execute(
                "DELETE FROM raffles WHERE last_seen < ?",
                (prune_before.isoformat(),),
            )

    def list_raffles(
        self,
        *,
        search: Optional[str] = None,
        max_odds: Optional[float] = None,
        ends_before: Optional[datetime] = None,
        sort: str = "deadline",
        limit: int = 50,
        offset: int = 0,
    ) -> List[dict]:
        query = ["SELECT source, raffle_id, title, prize, total_tickets, tickets_sold, ticket_price, deadline, url, last_seen FROM raffles"]
        params: list = []
        filters: list[str] = []

        if search:
            filters.append("(title LIKE ? OR prize LIKE ?)")
            term = f"%{search}%"
            params.extend([term, term])
        if max_odds is not None:
            filters.append("(tickets_sold IS NOT NULL AND total_tickets IS NOT NULL AND CAST(tickets_sold AS REAL) / total_tickets <= ?)")
            params.append(max_odds)
        if ends_before is not None:
            filters.append("(deadline IS NOT NULL AND deadline <= ?)")
            params.append(ends_before.isoformat())

        if filters:
            query.append("WHERE " + " AND ".join(filters))

        if sort == "odds":
            query.append("ORDER BY (CASE WHEN tickets_sold IS NULL OR total_tickets IS NULL THEN 1 ELSE CAST(tickets_sold AS REAL) / total_tickets END) ASC, deadline ASC")
        else:
            query.append("ORDER BY (deadline IS NULL) ASC, deadline ASC, last_seen DESC")

        query.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])

        with self.database.connect() as conn:
            cursor = conn.execute(" ".join(query), tuple(params))
            rows = cursor.fetchall()

        results: List[dict] = []
        for row in rows:
            deadline = parser.isoparse(row["deadline"]) if row["deadline"] else None
            odds = None
            if row["tickets_sold"] is not None and row["total_tickets"]:
                odds = row["tickets_sold"] / float(row["total_tickets"])
            results.append(
                {
                    "source": row["source"],
                    "raffle_id": row["raffle_id"],
                    "title": row["title"],
                    "prize": row["prize"],
                    "total_tickets": row["total_tickets"],
                    "tickets_sold": row["tickets_sold"],
                    "ticket_price": row["ticket_price"],
                    "deadline": deadline,
                    "url": row["url"],
                    "last_seen": parser.isoparse(row["last_seen"]),
                    "odds": odds,
                }
            )
        return results

    def last_updated(self) -> Optional[datetime]:
        with self.database.connect() as conn:
            cursor = conn.execute("SELECT MAX(last_seen) as ts FROM raffles")
            row = cursor.fetchone()
            if row and row["ts"]:
                return parser.isoparse(row["ts"])
            return None
