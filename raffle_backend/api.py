from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .repository import RaffleRepository


def _demo_raffles(now: datetime) -> list["RaffleModel"]:
    """Return a handful of demo raffles for environments without data."""

    return [
        RaffleModel(
            source="demo",
            raffle_id="demo-gadget-pack",
            title="Gadget Lovers Mega Bundle",
            prize="Latest smartphone, tablet, and wireless earbuds",
            total_tickets=500,
            tickets_sold=125,
            ticket_price=2.5,
            deadline=(now + timedelta(days=7)),
            url="https://example.com/raffles/gadget-pack",
            last_seen=now,
            odds=1 / 500,
        ),
        RaffleModel(
            source="demo",
            raffle_id="demo-weekend-getaway",
            title="Luxury Weekend Getaway",
            prize="Two-night stay at a 5-star countryside hotel",
            total_tickets=350,
            tickets_sold=48,
            ticket_price=5.0,
            deadline=(now + timedelta(days=14)),
            url="https://example.com/raffles/weekend-getaway",
            last_seen=now,
            odds=1 / 350,
        ),
        RaffleModel(
            source="demo",
            raffle_id="demo-gaming-setup",
            title="Ultimate Gaming Setup",
            prize="4K monitor, mechanical keyboard, and pro headset",
            total_tickets=750,
            tickets_sold=312,
            ticket_price=1.5,
            deadline=(now + timedelta(days=21)),
            url="https://example.com/raffles/gaming-setup",
            last_seen=now,
            odds=1 / 750,
        ),
    ]

class RaffleModel(BaseModel):
    source: str
    raffle_id: str
    title: str
    prize: str
    total_tickets: Optional[int]
    tickets_sold: Optional[int]
    ticket_price: Optional[float]
    deadline: Optional[datetime]
    url: str
    last_seen: datetime
    odds: Optional[float]


class PaginatedRaffleResponse(BaseModel):
    results: list[RaffleModel]
    count: int
    last_updated: Optional[datetime]


class RepositoryProvider:
    """FastAPI dependency wrapper for accessing the repository."""

    def __init__(self, repository: RaffleRepository) -> None:
        self.repository = repository

    def __call__(self) -> RaffleRepository:
        return self.repository


def create_app(repository: RaffleRepository) -> FastAPI:
    app = FastAPI(title="Raffle Dashboard API", version="0.1.0")
    repo_dependency = RepositoryProvider(repository)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/raffles", response_model=PaginatedRaffleResponse)
    def list_raffles(
        response: Response,
        search: Optional[str] = Query(None, description="Filter by title or prize keyword"),
        max_odds: Optional[float] = Query(None, ge=0.0, le=1.0, description="Only raffles with odds <= this value"),
        ends_before: Optional[datetime] = Query(None, description="Only raffles ending before this ISO timestamp"),
        sort: str = Query("deadline", pattern="^(deadline|odds)$"),
        limit: int = Query(50, ge=1, le=200),
        offset: int = Query(0, ge=0),
        repository: RaffleRepository = Depends(repo_dependency),
    ) -> PaginatedRaffleResponse:
        raffles = repository.list_raffles(
            search=search,
            max_odds=max_odds,
            ends_before=ends_before,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        last_updated = repository.last_updated()
        response.headers["Cache-Control"] = "no-store"
        if last_updated:
            response.headers["X-Last-Updated"] = last_updated.isoformat()
        if not raffles and last_updated is None:
            now = datetime.now(timezone.utc)
            demo_entries = _demo_raffles(now)
            response.headers["X-Last-Updated"] = now.isoformat()
            return PaginatedRaffleResponse(results=demo_entries, count=len(demo_entries), last_updated=now)

        return PaginatedRaffleResponse(
            results=[RaffleModel(**raffle) for raffle in raffles],
            count=len(raffles),
            last_updated=last_updated,
        )

    @app.get("/health")
    def health(repository: RaffleRepository = Depends(repo_dependency)) -> dict[str, str]:
        timestamp = repository.last_updated()
        return {
            "status": "ok",
            "last_updated": timestamp.isoformat() if timestamp else "never",
        }

    return app
