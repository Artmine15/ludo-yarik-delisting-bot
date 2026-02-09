import pytest
from common import parse_announcement_data

# A list of test cases, each with a title and the expected output
test_cases = [
    (
        "Binance Will Delist AION, MIR and ANC on 2022-11-28",
        ("AION, MIR, ANC", "2022-11-28", "См. анонс")
    ),
    (
        "Notice on the Delisting of Multiple Trading Pairs (2023-01-20)",
        ("⚠️ <b>Тикеры не найдены</b>", "2023-01-20", "См. анонс")
    ),
    (
        "Binance to Delist DNT, NBS and BTG on 2023-02-09 09:00 (UTC)",
        ("DNT, NBS, BTG", "2023-02-09", "09:00 (UTC)")
    ),
    (
        "Gentle Reminder: Bybit Will Delist the RSR/BTC Spot Trading Pair",
        ("RSR", "См. анонс", "См. анонс")
    ),
    (
        "Binance Futures Will Delist ALGO/BUSD and LUNA/BUSD Perpetual Contracts",
        ("ALGO, LUNA", "См. анонс", "См. анонс")
    ),
    (
        "Delisting of PNT/USDT",
        ("PNT", "См. анонс", "См. анонс")
    ),
    (
        "Notice Regarding the Removal of LITH/USDT from Spot Trading",
        ("LITH", "См. анонс", "См. анонс")
    )
]

@pytest.mark.parametrize("title, expected", test_cases)
def test_parse_announcement_data(title, expected):
    """
    Tests the parse_announcement_data function with various title formats.
    """
    assert parse_announcement_data(title) == expected

def test_parse_empty_title():
    """
    Tests the parser with an empty string.
    """
    assert parse_announcement_data("") == ("⚠️ <b>Тикеры не найдены</b>", "См. анонс", "См. анонс")
