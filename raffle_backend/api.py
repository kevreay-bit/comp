from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, Query, Response
from pydantic import BaseModel

from .repository import RaffleRepository


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
