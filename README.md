# comp

This repository contains a small collection of raffle scrapers that follow a
three-stage extraction strategy:

1. **Network discovery** – HTML responses are inspected for embedded JSON
   endpoints (for example, Shopify's `/products.json`). These endpoints are
   requested directly whenever the raw markup omits ticket counts or raffle
   deadlines.
2. **JavaScript rendering** – When the information is only available after the
   page executes JavaScript, the scraper falls back to a cached Playwright
   session. The helper waits for the configured selectors before extracting the
   rendered markup.
3. **Caching and rate limiting** – Playwright-backed requests are cached on
   disk and guarded by concurrency and interval controls to avoid tripping
   storefront rate limits.

## Layout

- `scrapers/base.py` – Common scraper interface and `ScraperResult` data class.
- `scrapers/utils.py` – Utilities for discovering JSON endpoints within HTML
  responses.
- `scrapers/playwright_fetcher.py` – Cached Playwright helper used by scrapers
  that require rendered HTML.
- `scrapers/shopify.py` – Shopify-specific scraper that prefers JSON endpoints
  and parses product inventory for ticket counts.
- `scrapers/raffle_api.py` – Generic scraper for custom raffle APIs that may
  expose raffle data after JavaScript execution.

## Running tests

```bash
pytest
```
