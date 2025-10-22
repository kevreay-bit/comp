# Raffle ingestion utilities

This repository provides a lightweight raffle ingestion pipeline backed by SQLite.

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. (Optional) Override the default database path or ingestion interval using
   environment variables:

   - `RAFFLES_DATABASE_URL` – defaults to `sqlite:///raffles.db`
   - `RAFFLES_INGEST_INTERVAL_SECONDS` – defaults to 300 seconds (5 minutes)

## Running an ingestion manually

Execute the ingestion script to run all scrapers, persist results, and prune stale
records:

```bash
python scripts/update_raffles.py
```

Use the `-v` flag to enable verbose logging.

## Scheduling ingestion

Launch the embedded APScheduler-based scheduler to run ingestion on a configurable
interval:

```bash
python -m app.scheduler
```

The scheduler logs successes and failures and keeps running until interrupted.
