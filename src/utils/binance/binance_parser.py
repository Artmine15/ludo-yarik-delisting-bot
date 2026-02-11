import re
from typing import Optional, List, Dict, Any

def parse_announcement_title(title: str) -> Dict[str, Optional[Any]]:
    """
    Parses the Binance announcement title to extract tickers and date.
    Args:
        title: The title string from the Binance announcement.
    Returns:
        A dictionary containing 'tickers' (list of strings) and 'date' (string).
        Missing values will be None or empty list. Time is assumed to be not in title.
    """
    extracted_data = {
        "tickers": [],
        "date": None,
        "time": None # Time is generally not present in the title
    }

    # Define common suffixes to remove from tickers for cleaner output
    common_ticker_suffixes = ["USDT", "PERP", "USD", "USDC", "BTC", "ETH", "BNB"] # Add more as needed
    
    # --- Extract Tickers ---
    potential_tickers = set()

    # Pattern for "Binance Will Delist ACA, CHESS, DATA, DF, GHST, NKN on YYYY-MM-DD"
    # This captures multiple tickers separated by commas and spaces.
    delist_match = re.search(r'Delist\s+([A-Z0-9,\s]+?)\s+on', title)
    if delist_match:
        tickers_str = delist_match.group(1).strip()
        # Split by comma and space, then clean
        for ticker_part in re.split(r'[, ]+', tickers_str):
            if ticker_part:
                potential_tickers.add(ticker_part.upper())
    
    # Pattern for "Binance Will List Token Name (TKN)" or "Delisting X"
    list_match = re.search(r'List\s+[A-Z][a-zA-Z\s]+?\s+\(([A-Z0-9]{2,10})\)', title)
    if list_match:
        potential_tickers.add(list_match.group(1).upper())
    
    # General pattern for capitalized words (potential tickers)
    # Be more selective than Bybit parser as title is shorter and more specific
    general_ticker_matches = re.findall(r'\b([A-Z0-9]{2,10})\b', title)
    for ticker in general_ticker_matches:
        # Exclude common non-ticker words, especially those found in titles
        if ticker.upper() not in ["BINANCE", "WILL", "LIST", "DELIST", "NOTICE", "OF", "REMOVAL", "SPOT", "TRADING", "PAIRS", "ON", "TOKEN", "NAME", "AND", "THE"]:
            potential_tickers.add(ticker.upper())

    # Filter and clean tickers by removing common suffixes
    cleaned_tickers = set()
    for ticker in potential_tickers:
        cleaned_ticker = ticker
        for suffix in common_ticker_suffixes:
            if cleaned_ticker.endswith(suffix) and len(cleaned_ticker) > len(suffix): # Ensure remaining part is not empty
                cleaned_ticker = cleaned_ticker[:-len(suffix)]
                break # Remove only one suffix type per ticker, prioritize the first match
        if cleaned_ticker: # Ensure ticker is not empty after cleaning
            cleaned_tickers.add(cleaned_ticker)

    extracted_data["tickers"] = sorted(list(cleaned_tickers))


    # --- Extract Date ---
    # Look for YYYY-MM-DD format, which is common in Binance titles
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', title)
    if date_match:
        extracted_data["date"] = date_match.group(1)
    
    # Also look for "MMM DD, YYYY" if it appears (less common in titles, more in descriptions)
    month_day_year_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}', title, re.IGNORECASE)
    if month_day_year_match:
        extracted_data["date"] = month_day_year_match.group(0)

    return extracted_data
