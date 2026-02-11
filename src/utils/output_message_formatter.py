from typing import List, Optional

def format_delisting_message(
    header: str,
    tickers: Optional[List[str]],
    date: Optional[str],
    time: Optional[str],
    announcement_url: str
) -> str:
    """
    Formats the delisting message for Telegram in HTML.
    Args:
        header: The main header for the announcement (e.g., "Bybit").
        tickers: A list of ticker symbols (e.g., ["OM", "MANTRA"]).
        date: The date of the delisting.
        time: The time of the delisting.
        announcement_url: The URL to the original announcement.
    Returns:
        A formatted HTML string for Telegram.
    """
    message_parts = []
    
    # Header
    message_parts.append(f"🚨 <b>{header}</b> DELISTING\n\n")

    # Tickers
    if tickers:
        formatted_tickers = [f"<code>${ticker}</code>" for ticker in tickers]
        message_parts.append(f"🪙 Монеты: {', '.join(formatted_tickers)}\n")

    # Date
    if date:
        message_parts.append(f"📅 Дата: {date}\n")

    # Time
    if time:
        message_parts.append(f"🕒 Время: {time}\n")

    # Announcement URL
    message_parts.append(f"\n📜 <a href=\"{announcement_url}\">Читать анонс</a>")

    return "".join(message_parts)
