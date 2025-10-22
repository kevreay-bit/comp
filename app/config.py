"""Configuration helpers for the raffle ingestion service."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class Settings:
    """Application settings with environment-based overrides."""

    database_url: str = os.getenv("RAFFLES_DATABASE_URL", "sqlite:///raffles.db")
    ingestion_interval: timedelta = timedelta(
        seconds=int(os.getenv("RAFFLES_INGEST_INTERVAL_SECONDS", "300"))
    )


def get_settings() -> Settings:
    """Return lazily constructed settings instance."""

    return Settings()
