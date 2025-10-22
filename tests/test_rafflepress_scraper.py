from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from scraper.sites.rafflepress import RafflePressScraper


class MockResponse:
    def __init__(self, text: str) -> None:
        self.text = text
        self.status_code = 200

    def raise_for_status(self) -> None:  # pragma: no cover - always OK in tests
        return None


def test_rafflepress_scraper_extracts_metrics():
    html = """
    <html><body>
    <div class="rafflepress-contest" data-total="300">
        <h2 class="rafflepress-title">Win an iPhone</h2>
        <div class="rafflepress-prize">iPhone 15 Pro</div>
        <span class="rafflepress-price">£3.00</span>
        <span class="rafflepress-progress__sold">120 sold</span>
        <span class="rafflepress-progress__remaining">180 remaining</span>
        <span class="rafflepress-countdown" data-end="2024-06-01T20:00:00Z">Ends soon</span>
        <a class="rafflepress-button" href="/competitions/win-iphone">Enter now</a>
    </div>
    </body></html>
    """

    session = Mock()
    session.get.return_value = MockResponse(html)

    scraper = RafflePressScraper(
        base_url="https://rafflepress.example",
        listing_path="/competitions",
        session=session,
        now=datetime(2024, 5, 1, tzinfo=timezone.utc),
    )

    competitions = scraper.scrape()
    assert len(competitions) == 1
    competition = competitions[0]
    assert competition.title == "Win an iPhone"
    assert competition.prize == "iPhone 15 Pro"
    assert float(competition.price) == pytest.approx(3.0)
    assert competition.tickets_total == 300
    assert competition.tickets_sold == 120
    assert competition.tickets_remaining == 180
    assert competition.sold_ratio == pytest.approx(0.4)
    assert competition.deadline == "2024-06-01T20:00:00+00:00"
    assert competition.url == "https://rafflepress.example/competitions/win-iphone"
