import re
from typing import Optional, List, Dict, Any

def parse_description(description: str) -> Dict[str, Optional[Any]]:
    """
    Parses the Bybit delisting description to extract tickers, date, and time.
    Args:
        description: The description string from the Bybit announcement.
    Returns:
        A dictionary containing 'tickers' (list of strings), 'date' (string),
        and 'time' (string). Missing values will be None or empty list.
    """
    extracted_data = {
        "tickers": [],
        "date": None,
        "time": None
    }

    # Define common suffixes to remove from tickers
    common_ticker_suffixes = ["USDT", "PERP", "USD", "USDC", "USDT", "ETH", "BTC"] # Add more as needed
    
    # --- Extract Tickers ---
    potential_tickers = set()

    # 1. Pattern to capture ticker before "Perpetual Contract" or similar phrases
    #    e.g., "delisting the SAROSUSDT Perpetual Contract" -> SAROSUSDT
    contract_match = re.search(r'delisting the ([A-Z0-9]{2,10})(?: Perpetual)? Contract', description)
    if contract_match:
        potential_tickers.add(contract_match.group(1).upper())
    
    # 2. Pattern for general delisted coins/tokens, e.g., "Delisting of COQ and VRA"
    #    This might capture multiple tickers separated by "and"
    delisting_of_match = re.findall(r'delisting (?:of )?([A-Z0-9]{2,10}(?: and [A-Z0-9]{2,10})*)', description, re.IGNORECASE)
    for match_group in delisting_of_match:
        # Split by " and " to handle multiple tickers in one match
        for ticker_part in re.split(r' and ', match_group):
            if ticker_part and ticker_part.upper() not in ["AND", "OF", "TO", "FOR", "WITH", "FROM", "VIA", "IN", "THE", "AM", "PM", "UTC", "AT"]:
                potential_tickers.add(ticker_part.upper())

    # 3. Specific pattern for "Token swap and rebranding of MANTRA (OM) to MANTRA (MANTRA)"
    rebranding_match = re.search(r'rebranding of \s*(\S+)\s*\(([A-Z0-9]{2,10})\)', description, re.IGNORECASE)
    if rebranding_match:
        potential_tickers.add(rebranding_match.group(2).upper())

    # Filter and clean tickers
    cleaned_tickers = set()
    for ticker in potential_tickers:
        cleaned_ticker = ticker
        for suffix in common_ticker_suffixes:
            if cleaned_ticker.endswith(suffix):
                # Remove suffix if it's the last part and the remaining part is still a valid ticker length
                if len(cleaned_ticker) - len(suffix) >= 2:
                    cleaned_ticker = cleaned_ticker[:-len(suffix)]
                break # Only remove one suffix type per ticker, prioritize the first match
        # Final check to ensure it's not a common word that slipped through
        if cleaned_ticker and cleaned_ticker not in ["AND", "OF", "TO", "FOR", "WITH", "FROM", "VIA", "IN", "THE", "AM", "PM", "UTC", "AT"]:
            cleaned_tickers.add(cleaned_ticker)


    extracted_data["tickers"] = sorted(list(cleaned_tickers))

    # --- Extract Date ---
    # Prioritize specific formats
    # Example: "at Feb 11, 2026", "Feb 11, 2026"
    date_patterns = [
        r'(?:at |on )?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}', # "at Feb 11, 2026" or "Feb 11, 2026"
        r'(?:on the )?\d{1,2}(?:st|nd|rd|th)?\s+(?:of\s+)?(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4}', # "11th of Feb 2026"
        r'(\d{4}-\d{2}-\d{2})', # YYYY-MM-DD
        r'(\d{1,2}/\d{1,2}/\d{4})' # MM/DD/YYYY or DD/MM/YYYY
    ]
    for pattern in date_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            extracted_data["date"] = match.group(0).strip()
            # If it started with "at " or "on ", remove it for cleaner output
            if extracted_data["date"].lower().startswith("at "):
                extracted_data["date"] = extracted_data["date"][3:]
            elif extracted_data["date"].lower().startswith("on "):
                extracted_data["date"] = extracted_data["date"][3:]
            break

    # --- Extract Time ---
    # Example: "9:00AM UTC", "at 9:00AM UTC"
    time_patterns = [
        r'(?:at )?(\d{1,2}:\d{2}(?:AM|PM)?\s*UTC)', # "at 9:00AM UTC" or "9:00AM UTC"
        r'(?:at )?(\d{1,2}:\d{2}(?:AM|PM)?)',       # "at 9:00AM" or "9:00AM"
        r'(\d{1,2}:\d{2})'                          # "09:00"
    ]
    for pattern in time_patterns:
        match = re.search(pattern, description, re.IGNORECASE)
        if match:
            extracted_data["time"] = match.group(1).strip()
            break

    return extracted_data
