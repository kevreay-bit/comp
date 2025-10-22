# Raffle API Service

This repository contains a FastAPI service that exposes raffle entries scraped from
external sources. The `/api/raffles` endpoint provides sorting, filtering, and
pagination options so the frontend can request exactly the slices of data it needs
without additional post-processing.

## Features

- **Filtering** – limit raffles by maximum odds, a deadline cutoff, or keyword
  searches across names and descriptions.
- **Sorting** – order results by `deadline` or `odds` via the `sort` query parameter.
- **Pagination** – `page` and `page_size` parameters avoid returning more data than
  the client can display.
- **Caching & ETags** – the service caches query responses for a short period and
  issues ETags so repeat requests can take advantage of `If-None-Match` headers.

## Running locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The service automatically creates the SQLite database (`raffles.db`) on startup.
You can populate the database using your scraper or by inserting rows manually via
any SQLite client.

## Example request

```
GET /api/raffles?sort=odds&max_odds=0.05&ends_before=2024-07-01T00:00:00Z&q=console&page=1&page_size=20
```

The response payload includes the filtered raffle data and pagination metadata as
well as an `ETag` header that can be reused in subsequent requests.
