import pytest
from common import parse_article_content

# Sample HTML content for Binance
BINANCE_HTML = """
<html><body>
    <h1>Notice on the Removal of Spot Trading Pairs - 2025-02-28</h1>
    <p>Fellow Binancians,</p>
    <p>At Binance, we periodically review each digital asset we list to ensure that it continues to meet the high level of standard we expect. When a coin or token no longer meets this standard, or the industry changes, we conduct a more in-depth review and potentially delist it. We believe this best protects all our users.</p>
    <p>Based on our most recent reviews, we have decided to delist and cease trading on all spot trading pairs for the following token(s) at <strong>2025-02-28 03:00 (UTC)</strong>:</p>
    <ul>
        <li><strong>Aragon (ANT)</strong></li>
        <li><strong>Multi-collateral Dai (DAI)</strong></li>
    </ul>
    <p>The exact trading pairs being removed are: <strong>ANT/BTC, ANT/USDT, DAI/BUSD.</strong></p>
</body></html>
"""

# Sample HTML content for Bybit
BYBIT_HTML = """
<html><head><title>Delisting of CUDISUSDT Perpetual Contract</title></head>
<body>
    <p>We will be delisting the <strong>CUDISUSDT</strong> Perpetual Contract at <strong>9AM UTC on Feb 11, 2026</strong>.</p>
    <p>Another pair is TEST/USDT</p>
</body></html>
"""

# Test cases for the new HTML parser
# Each case: (html_content, url, expected_output)
test_cases = [
    (
        BINANCE_HTML,
        "https://www.binance.com/en/support/announcement/test-1",
        ("<code>$ANT</code>, <code>$DAI</code>", "2025-02-28", "03:00 (UTC)")
    ),
    (
        BYBIT_HTML,
        "https://announcements.bybit.com/en/article/test-2",
        ("<code>$CUDIS</code>, <code>$TEST</code>", "Feb 11, 2026", "9AM UTC")
    ),
    (
        "<html><body>No info here</body></html>",
        "https://www.binance.com/test-3",
        ("⚠️ <b>Тикеры не найдены</b>", "См. анонс", "См. анонс")
    )
]

@pytest.mark.parametrize("html, url, expected", test_cases)
def test_parse_article_content(html, url, expected):
    """
    Tests the parse_article_content function with various HTML contents.
    """
    assert parse_article_content(html, url) == expected

def test_unknown_url_parser():
    """
    Tests that the parser returns a default value for an unknown URL.
    """
    html = "<html><body><strong>GIBBERISH/BTC</strong></body></html>"
    url = "https://some-other-exchange.com"
    expected = ("⚠️ <b>Тикеры не найдены</b>", "См. анонс", "См. анонс")
    assert parse_article_content(html, url) == expected
