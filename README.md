# Raffle dashboard

This repository contains the ingestion pipeline and API required to power a raffle competition dashboard. It also ships with a lightweight browser UI that polls the API for the latest raffles.

## Features

- **Ingestion pipeline** – normalises raffle data from pluggable scrapers and stores it in SQLite.
- **Scheduled updates** – APScheduler keeps the database fresh by running scrapers on an interval.
- **FastAPI service** – exposes `GET /raffles` with filtering, sorting by odds or deadline, and cache-busting headers for real-time dashboards.
- **Browser dashboard** – a vanilla JavaScript page that refreshes every 30 seconds and lets users refine results via search, sort, and filters.

## Requirements

- Python 3.10+
- Node.js is **not** required – the frontend is a static HTML file.

Install Python dependencies:

```bash
pip install -e .
```

## Project layout

```
.
├── pyproject.toml          # Python project configuration and dependencies
├── raffle_backend/         # FastAPI service, ingestion pipeline, scheduler helpers
├── scripts/                # Command line utilities (ingestion runner)
└── frontend/               # Static dashboard page that consumes the API
```

## Step-by-step usage (no prior experience needed)

### 1. Run the ingestion pipeline once

Populate the SQLite database (stored at `data/raffles.db`) with the built-in demo scraper.

```bash
python -m scripts.update_raffles
```

The command prints how many raffles were processed.

### 2. Start the API server

Launch the FastAPI service using Uvicorn:

```bash
uvicorn raffle_backend.main:app --reload
```

The API becomes available at <http://localhost:8000>. Visit <http://localhost:8000/docs> for interactive documentation.

> **Tip:** `raffle_backend/main.py` also exposes a `run()` helper if you prefer invoking `python -m raffle_backend.main`.

### 3. Open the live dashboard

Open `frontend/index.html` in your browser (double-click it or run `python -m http.server` and visit `http://localhost:8000` depending on your preference). The page polls the API every 30 seconds and displays the latest raffles, allowing you to:

- Search by title or prize
- Sort by earliest deadline or best odds
- Filter by maximum odds or a “ends before” timestamp

The built-in demo scraper seeds the database with sample data so you can see the UI in action immediately. Replace `DummyScraper` inside `raffle_backend/main.py` with the real scrapers when they are ready.

## Configuration

- Database location: default `data/raffles.db`. Override via `python -m scripts.update_raffles --database <path>` or by adjusting `DEFAULT_DB_PATH` in `raffle_backend/main.py`.
- Scheduler interval: change the `interval_minutes` argument passed to `IngestionScheduler` in `create_service()`.

## Next steps

- Plug in real scraper implementations using the `RaffleScraper` protocol from `raffle_backend/ingestion.py`.
- Extend the frontend styling or replace it with your framework of choice.
- Deploy the FastAPI service behind a production-ready ASGI server (e.g., Uvicorn + Gunicorn) and host the static dashboard from a CDN or static site host.
