import re
from datetime import datetime
from bs4 import BeautifulSoup

# Base currencies and keywords to exclude from ticker results.
EXCLUSION_LIST = {'USDT', 'USDC', 'BTC', 'ETH', 'PERPETUAL', 'CONTRACT', 'ALL', 'SPOT'}

def _parse_tickers(text):
    """
    Parses text to extract crypto tickers, handling various formats.
    """
    potential_tickers_re = re.compile(r'\b[A-Z0-9]{2,10}\b')
    pairs_re = re.compile(r'\b([A-Z0-9]{2,10})/([A-Z0-9]{2,10})\b')
    
    found_tickers = set(potential_tickers_re.findall(text))
    
    for match in pairs_re.finditer(text):
        found_tickers.add(match.group(1))

    cleaned_tickers = {t for t in found_tickers if t not in EXCLUSION_LIST}
    
    final_tickers = set()
    for ticker in cleaned_tickers:
        normalized = False
        for base in EXCLUSION_LIST:
            if ticker.endswith(base) and len(ticker) > len(base):
                final_tickers.add(ticker[:-len(base)])
                normalized = True
                break
        if not normalized:
            final_tickers.add(ticker)
            
    return sorted([t for t in final_tickers if t not in EXCLUSION_LIST])

def _normalize_date_time(date_str, time_str):
    """
    Normalizes raw date and time strings into a consistent format (YYYY-MM-DD, HH:MM).
    """
    norm_date = "См. анонс"
    if date_str:
        try:
            # Handles "YYYY-MM-DD" and "Month Day, YYYY"
            dt_obj = datetime.strptime(date_str, '%Y-%m-%d')
            norm_date = dt_obj.strftime('%Y-%m-%d')
        except ValueError:
            try:
                dt_obj = datetime.strptime(date_str, '%B %d, %Y')
                norm_date = dt_obj.strftime('%Y-%m-%d')
            except ValueError:
                norm_date = date_str # Keep original if format is unexpected

    norm_time = "См. анонс"
    if time_str:
        time_str_cleaned = time_str.upper().replace(" ", "")
        try:
            # Handles "8AM", "10PM"
            dt_obj = datetime.strptime(time_str_cleaned, '%I%p')
            norm_time = dt_obj.strftime('%H:%M')
        except ValueError:
            try:
                 # Handles "10:00"
                dt_obj = datetime.strptime(time_str_cleaned, '%H:%M')
                norm_time = dt_obj.strftime('%H:%M')
            except ValueError:
                norm_time = time_str # Keep original if format is unexpected

    return norm_date, norm_time

def _parse_date_time_by_proximity(text):
    """
    Finds date/time by calculating the proximity to delisting keywords.
    Best for unstructured text like Bybit announcements.
    """
    date_re = re.compile(r'(\d{4}-\d{2}-\d{2}|\w+\s\d{1,2},\s\d{4})')
    time_re = re.compile(r'(\d{1,2}:\d{2}|\d{1,2}\s?[AP]M)(?:\s*\(?UTC\)?)?')
    keywords = ["will terminate trading", "cease trading", "delist", "delisting of"]
    
    date_matches = list(date_re.finditer(text))
    keyword_matches = [m for k in keywords for m in re.finditer(k, text, re.IGNORECASE)]

    if not date_matches: return None, None
    if not keyword_matches:
        date = date_matches[0].group(0)
        time_match = time_re.search(text[date_matches[0].end():date_matches[0].end() + 30])
        return date, time_match.group(1).strip() if time_match else None

    best_date, min_dist = None, float('inf')
    for d_match in date_matches:
        for k_match in keyword_matches:
            dist = abs(d_match.start() - k_match.start())
            if dist < min_dist:
                min_dist, best_date = dist, d_match
    
    date_str = best_date.group(0)
    window = text[max(0, best_date.start() - 30):best_date.end() + 30]
    time_match = time_re.search(window)
    time_str = time_match.group(1).strip() if time_match else None
    
    return date_str, time_str

def _parse_binance_html(soup):
    """
    Parses Binance announcement HTML. It prioritizes the title for the date.
    """
    title_text = ""
    if soup.h1: title_text = soup.h1.get_text(strip=True)
    elif soup.h2: title_text = soup.h2.get_text(strip=True)

    date_re = re.compile(r'(\d{4}-\d{2}-\d{2}|\w+\s\d{1,2},\s\d{4})')
    time_re = re.compile(r'(\d{1,2}:\d{2}|\d{1,2}\s?[AP]M)(?:\s*\(?UTC\)?)?')

    # Priority search for date in title
    date_match = date_re.search(title_text)
    date_str = date_match.group(0) if date_match else None

    full_text = soup.get_text(separator=' ', strip=True)
    if not date_str: # Fallback to full text if no date in title
        date_match = date_re.search(full_text)
        date_str = date_match.group(0) if date_match else None

    time_match = time_re.search(full_text)
    time_str = time_match.group(1).strip() if time_match else None
    
    tickers = _parse_tickers(full_text)
    return tickers, date_str, time_str

def _parse_bybit_html(soup):
    """
    Parses Bybit announcement HTML using proximity search for date/time.
    """
    text = soup.get_text(separator=' ', strip=True)
    tickers = _parse_tickers(text)
    date_str, time_str = _parse_date_time_by_proximity(text)
    return tickers, date_str, time_str

def parse_article_content(html_content, url):
    """
    Main function to parse delisting data from HTML content.
    It cleans HTML, routes to the correct parser, and normalizes the output.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    if "binance.com" in url:
        tickers, date, time = _parse_binance_html(soup)
    elif "bybit.com" in url:
        tickers, date, time = _parse_bybit_html(soup)
    else:
        return "⚠️ <b>Парсер не реализован</b>", "<i>См. анонс</i>", "<i>См. анонс</i>"

    formatted_tickers = ', '.join([f"<code>{t}</code>" for t in tickers]) if tickers else "⚠️ <b>Тикеры не найдены</b>"
    norm_date, norm_time = _normalize_date_time(date, time)
    
    return formatted_tickers, norm_date, norm_time