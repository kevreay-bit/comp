from scrapers.utils import discover_json_endpoints, iter_json_candidates


def test_discover_json_endpoints_extracts_links():
    html = '''
    <html>
        <script src="/products.json"></script>
        <div data-endpoint="/raffles/api"></div>
    </html>
    '''
    endpoints = discover_json_endpoints(html, "https://example.com")
    assert "https://example.com/products.json" in endpoints
    assert "https://example.com/raffles/api" in endpoints


def test_iter_json_candidates_builds_urls():
    urls = list(iter_json_candidates("https://example.com", ["foo"]))
    assert "https://example.com/collections/foo/products.json" in urls
    assert "https://example.com/foo.json" in urls
