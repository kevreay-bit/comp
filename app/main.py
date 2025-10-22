"""FastAPI application exposing raffle data with rich filtering capabilities."""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from .cache import cache
from .database import SessionLocal, engine
from .models import Base, Raffle
from .schemas import PaginatedRaffleResponse, RaffleRead

app = FastAPI(title="Raffle API", version="1.0.0")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


def validate_sort(sort: str | None) -> str:
    if sort is None:
        return "deadline"
    sort = sort.lower()
    if sort not in {"deadline", "odds"}:
        raise HTTPException(status_code=400, detail="Invalid sort parameter")
    return sort


def build_cache_key(
    *,
    sort: str,
    max_odds: float | None,
    ends_before: datetime | None,
    keyword: str | None,
    page: int,
    page_size: int,
) -> tuple:
    return (
        sort,
        round(max_odds, 6) if max_odds is not None else None,
        ends_before.isoformat() if ends_before else None,
        keyword.lower() if keyword else None,
        page,
        page_size,
    )


def parse_if_none_match(header_value: str | None) -> set[str]:
    if not header_value:
        return set()
    return {
        tag.strip().strip('"')
        for tag in header_value.split(",")
        if tag.strip()
    }


def format_etag(etag: str) -> str:
    return f'"{etag}"'


@app.get("/api/raffles", response_model=PaginatedRaffleResponse)
def list_raffles(
    request: Request,
    response: Response,
    sort: Annotated[str | None, Query(description="Sort by odds or deadline")] = None,
    max_odds: Annotated[float | None, Query(ge=0, description="Upper bound for raffle odds")] = None,
    ends_before: Annotated[
        datetime | None,
        Query(description="Only include raffles ending before this ISO timestamp"),
    ] = None,
    keyword: Annotated[str | None, Query(alias="q", description="Keyword search")] = None,
    page: Annotated[int, Query(ge=1, description="Page number")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Results per page")] = 25,
    db: Session = Depends(get_db),
) -> PaginatedRaffleResponse:
    sort_value = validate_sort(sort)
    cache_key = build_cache_key(
        sort=sort_value,
        max_odds=max_odds,
        ends_before=ends_before,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )

    cached = cache.get(cache_key)
    if cached:
        if_none_match = parse_if_none_match(request.headers.get("if-none-match"))
        etag_header = format_etag(cached.etag)
        if cached.etag in if_none_match:
            return Response(status_code=304, headers={"ETag": etag_header})
        response.headers["ETag"] = etag_header
        return PaginatedRaffleResponse.parse_obj(cached.data)

    query = select(Raffle)
    count_query = select(func.count()).select_from(Raffle)

    filters = []
    if max_odds is not None:
        filters.append(Raffle.odds <= max_odds)
    if ends_before is not None:
        filters.append(Raffle.deadline <= ends_before)
    if keyword:
        like_pattern = f"%{keyword.lower()}%"
        filters.append(
            or_(
                func.lower(Raffle.name).like(like_pattern),
                func.lower(func.coalesce(Raffle.description, "")).like(like_pattern),
            )
        )

    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)

    if sort_value == "deadline":
        query = query.order_by(Raffle.deadline.asc())
    else:
        query = query.order_by(Raffle.odds.asc(), Raffle.deadline.asc())

    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    total = db.execute(count_query).scalar_one()
    items = db.execute(query).scalars().all()

    data = [RaffleRead.from_orm(item) for item in items]
    payload = PaginatedRaffleResponse(
        data=data,
        meta={"page": page, "page_size": page_size, "total": total},
    )
    encoded_payload = jsonable_encoder(payload)
    entry = cache.set(cache_key, encoded_payload)

    etag_header = format_etag(entry.etag)
    response.headers["ETag"] = etag_header
    if entry.etag in parse_if_none_match(request.headers.get("if-none-match")):
        return Response(status_code=304, headers={"ETag": etag_header})

    return payload
