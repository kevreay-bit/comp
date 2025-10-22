from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest

from scraper.sites.shopify import ShopifyStoreScraper


class MockResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - always OK in tests
        return None


@pytest.fixture()
def mock_session(monkeypatch):
    session = Mock()

    page_one = """
    <html><body>
    <article class="product-card" data-total="1000" data-sold="400">
        <a class="product-card__link" href="/products/prize-one">
            <div class="product-card__title">Win a Campervan</div>
        </a>
        <div class="product-card__subtitle">Luxury Camper</div>
        <span class="price-item--regular">£2.99</span>
        <div class="product-card__countdown">Draw Date: 2024-05-12 20:00</div>
    </article>
    <article class="product-card" data-total="500">
        <a class="product-card__link" href="/products/prize-two">
            <div class="product-card__title">Win a PS5</div>
        </a>
        <div class="progress__remaining">150 tickets remaining</div>
        <div class="progress__sold">350 sold</div>
        <span class="price-item--regular">£1.50</span>
        <div class="product-card__countdown">2 days 3 hours</div>
    </article>
    <a rel="next" href="?page=2">Next</a>
    </body></html>
    """

    page_two = """
    <html><body>
    <article class="product-card" data-total="200" data-remaining="50">
        <a class="product-card__link" href="/products/prize-three">
            <div class="card__heading">Win Cash</div>
        </a>
        <span class="price-item--regular">£0.99</span>
        <div class="product-card__countdown">2024-05-15T12:00:00Z</div>
    </article>
    </body></html>
    """

    responses = {
        "https://example.com/collections/all": MockResponse(page_one),
        "https://example.com/collections/all?page=2": MockResponse(page_two),
    }

    def fake_get(url, headers=None, timeout=None):  # pragma: no cover - helper
        return responses[url]

    session.get.side_effect = fake_get
    return session


def test_shopify_scraper_parses_listings(mock_session):
    now = datetime(2024, 5, 1, tzinfo=timezone.utc)
    scraper = ShopifyStoreScraper(
        store_domain="https://example.com",
        session=mock_session,
        now=now,
    )

    competitions = scraper.scrape()
    assert len(competitions) == 3

    first = competitions[0]
    assert first.title == "Win a Campervan"
    assert first.prize == "Luxury Camper"
    assert float(first.price) == pytest.approx(2.99)
    assert first.tickets_total == 1000
    assert first.tickets_sold == 400
    assert first.sold_ratio == pytest.approx(0.4)
    assert first.deadline.startswith("2024-05-12T20:00")
    assert first.url == "https://example.com/products/prize-one"

    second = competitions[1]
    assert second.tickets_total == 500
    assert second.tickets_remaining == 150
    assert second.tickets_sold == 350
    assert second.sold_ratio == pytest.approx(0.7)
    expected_deadline = (now + timedelta(days=2, hours=3)).isoformat()
    assert second.deadline == expected_deadline

    third = competitions[2]
    assert third.title == "Win Cash"
    assert third.tickets_total == 200
    assert third.tickets_remaining == 50
    assert third.tickets_sold == 150
    assert third.sold_ratio == pytest.approx(0.75)
    assert third.url == "https://example.com/products/prize-three"
