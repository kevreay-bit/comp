"""Configuration helpers for raffle ingestion."""
from __future__ import annotations

import os
from pathlib import Path


def get_database_url() -> str:
    """Return the database URL for the raffles store.

    Defaults to a SQLite database stored in the repository root.
    """

    return os.getenv("RAFFLES_DATABASE_URL", f"sqlite:///{get_default_db_path()}")


def get_default_db_path() -> Path:
    """Location of the default SQLite database file."""

    root = Path(__file__).resolve().parents[1]
    return root / "raffles.db"


def get_update_interval_seconds() -> int:
    """Return the update interval for the scheduler in seconds."""

    return int(os.getenv("RAFFLES_UPDATE_INTERVAL", "900"))


def get_prune_hours() -> float:
    """Return number of hours after which unseen raffles are pruned."""

    return float(os.getenv("RAFFLES_PRUNE_HOURS", "24"))
