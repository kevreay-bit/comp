"""Pydantic schemas for the raffle API service."""
from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, Field


class RaffleBase(BaseModel):
    name: str
    description: str | None = None
    odds: float = Field(..., ge=0)
    deadline: datetime


class RaffleRead(RaffleBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class PaginationMeta(BaseModel):
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1)
    total: int = Field(..., ge=0)


class PaginatedRaffleResponse(BaseModel):
    data: List[RaffleRead]
    meta: PaginationMeta
