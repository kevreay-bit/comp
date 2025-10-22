# comp raffle scrapers

This repository provides a modular scraping framework for raffle web sites. The
`scraper/` package exposes a reusable `BaseScraper` class with pluggable
`fetch()` and `parse()` hooks, concrete implementations for two fictional
raffle providers, and a shared queue that receives normalized output records.

## Components

- `scraper/base.py` – shared orchestration logic, HTTP retry helpers, and
  logging instrumentation.
- `scraper/models.py` – dataclass describing the normalized raffle payload.
- `scraper/pipeline.py` – thread-safe queue that collects scraper output.
- `scraper/sites/` – site-specific scrapers for static (requests +
  BeautifulSoup) and dynamic (Playwright) pages.
- `scraper/runner.py` – convenience utilities to run the scrapers together.

## Usage

```bash
python -m scraper.runner
```

The runner configures logging, executes each scraper, and leaves the results in
`scraper.pipeline.raffle_queue`. Access `raffle_queue.pop()` to retrieve
`scraper.models.RaffleEntry` instances or call `RaffleEntry.as_dict()` for a JSON
ready representation.
