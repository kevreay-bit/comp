# Raffle ingestion utilities

This repository provides a lightweight raffle ingestion pipeline backed by SQLite.

## Quick start (layman's terms)

1. **Make sure Python 3.10+ is installed.** On macOS/Linux it usually already is.
   On Windows you can get it from [python.org](https://www.python.org/downloads/).

2. **Open a terminal and move into this project folder.** For example:

   ```bash
   cd path/to/this/repo
   ```

3. **Create a Python sandbox and install the only dependency.**

   ```bash
   python -m venv .venv          # create an isolated Python
   source .venv/bin/activate     # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Run the one-off updater.** It fetches raffle data and saves it in a
   `raffles.db` file sitting next to the code.

   ```bash
   python scripts/update_raffles.py
   ```

5. **Peek at the saved raffles (optional).** Install the SQLite CLI
   (`sudo apt install sqlite3`, or use [DB Browser for SQLite](https://sqlitebrowser.org/)),
   then run:

   ```bash
   sqlite3 raffles.db "SELECT source, raffle_id, title, deadline FROM raffles;"
   ```

That’s it—you now have a tiny database of the latest raffle snapshots.

## Configuration knobs

You can override the default database path or ingestion interval using
environment variables:

- `RAFFLES_DATABASE_URL` – defaults to `sqlite:///raffles.db`
- `RAFFLES_INGEST_INTERVAL_SECONDS` – defaults to 300 seconds (5 minutes)

## Running an ingestion manually

Execute the ingestion script to run all scrapers, persist results, and prune stale
records:

```bash
python scripts/update_raffles.py
```

Use the `-v` flag to enable verbose logging. Pass `--database-url` to override the
database connection for a single run:

```bash
python scripts/update_raffles.py --database-url sqlite:///tmp/raffles.db
```

## Scheduling ingestion

Launch the embedded APScheduler-based scheduler to run ingestion on a configurable
interval:

```bash
python -m app.scheduler
```

The scheduler logs successes and failures and keeps running until interrupted.
