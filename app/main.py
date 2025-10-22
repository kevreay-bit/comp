"""FastAPI application exposing raffle data and scheduling ingestion."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import BackgroundTasks, FastAPI, HTTPException

from raffles.db import fetch_all, init_db
from raffles.settings import get_update_interval_seconds
from scripts.update_raffles import run_ingestion

LOGGER = logging.getLogger(__name__)

app = FastAPI(title="Raffle Aggregator")
scheduler = AsyncIOScheduler()


def _schedule_ingestion() -> None:
    interval_seconds = get_update_interval_seconds()
    LOGGER.info("Scheduling ingestion every %s seconds", interval_seconds)
    scheduler.add_job(
        run_ingestion,
        trigger=IntervalTrigger(seconds=interval_seconds),
        id="raffle-ingestion",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )


@app.on_event("startup")
async def on_startup() -> None:
    logging.basicConfig(level=logging.INFO)
    init_db()
    if not scheduler.running:
        scheduler.start()
    _schedule_ingestion()
    LOGGER.info("Application startup complete")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
    LOGGER.info("Application shutdown complete")


@app.get("/health")
async def healthcheck() -> Dict[str, Any]:
    return {"status": "ok"}


@app.get("/raffles")
async def list_raffles() -> List[Dict[str, Any]]:
    return list(fetch_all())


@app.post("/raffles/update")
async def trigger_update(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    try:
        background_tasks.add_task(run_ingestion)
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Failed to schedule manual update")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"status": "scheduled"}


__all__ = ["app"]
