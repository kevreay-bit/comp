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

> **Having trouble on Windows?** Some Windows editors can save `pyproject.toml` with a byte-order mark, which prevents `pip install -e .` from parsing the file and raises a `TOMLDecodeError`. If that happens, install the dependencies directly with:

```bash
pip install -r requirements.txt
```

> **Getting `Invalid requirement: diff --git ...`?** That message means the file was created from a Git diff instead of the raw contents. Open `requirements.txt`, delete everything inside, and replace it with just:
>
> ```text
> fastapi>=0.109.0
> uvicorn[standard]>=0.24.0
> python-dateutil>=2.8.2
> apscheduler>=3.10.4
> ```
>
> Save the file and rerun `pip install -r requirements.txt`.

This installs the FastAPI, Uvicorn, APScheduler, and `python-dateutil` packages the project depends on.

## Project layout

```
.
├── pyproject.toml          # Python project configuration and dependencies
├── raffle_backend/         # FastAPI service, ingestion pipeline, scheduler helpers
├── scripts/                # Command line utilities (ingestion runner)
└── frontend/               # Static dashboard page that consumes the API
```

## Step-by-step usage (no prior experience needed)

### 0. Install the Python dependencies

Before running any scripts, install the project requirements (this only needs to be done once per environment):

```bash
pip install -e .
```

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

> **Windows tip:** If PowerShell says `'uvicorn' is not recognized`, run the command through Python instead:
>
> ```bash
> python -m uvicorn raffle_backend.main:app --reload
> ```
>
> Alternatively, add `%APPDATA%\Python\Python3x\Scripts` (replace `3x` with your Python version) to your `PATH` so the `uvicorn` executable is available directly.

> **Tip:** `raffle_backend/main.py` also exposes a `run()` helper if you prefer invoking `python -m raffle_backend.main`.

### 3. Open the live dashboard

Open `frontend/index.html` in your browser (double-click it or run `python -m http.server` and visit `http://localhost:8000` depending on your preference). The page polls the API every 30 seconds and displays the latest raffles, allowing you to:

- Search by title or prize
- Sort by earliest deadline or best odds
- Filter by maximum odds or a “ends before” timestamp

The built-in demo scraper seeds the database with sample data so you can see the UI in action immediately. Even if you skip the ingestion step, the API now returns a few placeholder raffles so you can confirm the dashboard wiring before pointing it at real data. Replace `DummyScraper` inside `raffle_backend/main.py` with the real scrapers when they are ready.

#### Dashboard troubleshooting

- If the table stays on “Loading raffles…” use the **Check API** button near the top of the page. It pings `<API>/health` and reports whether the backend is reachable.
- A red “Offline” badge means the browser could not reach the API. Confirm the terminal running `python -m uvicorn raffle_backend.main:app --reload` is still active and that `python -m scripts.update_raffles` completed successfully at least once.
- You can also open <http://localhost:8000/raffles> directly in a browser tab to confirm the API returns JSON data.

## Configuration

- Database location: default `data/raffles.db`. Override via `python -m scripts.update_raffles --database <path>` or by adjusting `DEFAULT_DB_PATH` in `raffle_backend/main.py`.
- Scheduler interval: change the `interval_minutes` argument passed to `IngestionScheduler` in `create_service()`.

## Next steps

- Plug in real scraper implementations using the `RaffleScraper` protocol from `raffle_backend/ingestion.py`.
- Extend the frontend styling or replace it with your framework of choice.
- Deploy the FastAPI service behind a production-ready ASGI server (e.g., Uvicorn + Gunicorn) and host the static dashboard from a CDN or static site host.
