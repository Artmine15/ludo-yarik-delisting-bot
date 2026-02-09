import os
import json
import re
import logging
import boto3
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# --- Environment Variables ---
BOT_TOKEN = os.getenv('BOT_TOKEN')
CHAT_IDS_STRING = os.getenv('CHAT_IDS', '[]')
BUCKET_NAME = os.getenv('BUCKET_NAME')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

s3_client = boto3.client(
    service_name='s3',
    endpoint_url='https://storage.yandexcloud.net',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

def get_headers():
    return {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

def _parse_binance_html(soup):
    """Helper function to parse Binance announcement HTML."""
    tickers = set()
    # Find all strong tags, as they often contain tickers.
    for strong_tag in soup.find_all('strong'):
        text = strong_tag.get_text(strip=True)
        # Regex to find trading pairs like ABC/XYZ
        found_pairs = re.findall(r'\b[A-Z0-9]{2,10}/[A-Z0-9]{2,10}\b', text)
        for pair in found_pairs:
            # Add the base asset of the pair
            tickers.add(pair.split('/')[0])

    article_text = soup.get_text()
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', article_text)
    time_match = re.search(r'(\d{2}:\d{2})\s*\(UTC\)', article_text)

    if tickers:
        formatted_tickers = ', '.join([f"<code>${t}</code>" for t in sorted(list(tickers))])
    else:
        formatted_tickers = "⚠️ <b>Тикеры не найдены</b>"
    formatted_date = date_match.group(1) if date_match else "См. анонс"
    formatted_time = f"{time_match.group(1)} (UTC)" if time_match else "См. анонс"
    
    return formatted_tickers, formatted_date, formatted_time

def _parse_bybit_html(soup):
    """Helper function to parse Bybit announcement HTML."""
    article_text = soup.get_text()
    
    # Bybit often mentions the pair in the title or first paragraph.
    # A simple regex for pairs is a good starting point.
    tickers = set(re.findall(r'\b([A-Z0-9]{2,10})/([A-Z0-9]{2,10})\b', article_text))
    # For contract names like 'CUDISUSDT'
    contract_tickers = set(re.findall(r'Delisting of (\w+)\s', article_text, re.IGNORECASE))
    
    all_tickers = {pair[0] for pair in tickers}
    for contract in contract_tickers:
        # Avoid adding common currency names if they are part of the contract name
        if contract.upper() not in ['USDT', 'USDC', 'BTC', 'PERPETUAL', 'CONTRACT']:
             all_tickers.add(contract.upper())

    date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\w+\s\d{1,2},\s\d{4})', article_text)
    time_match = re.search(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?\s*\(?UTC\)?)', article_text)

    if all_tickers:
        formatted_tickers = ', '.join([f"<code>${t}</code>" for t in sorted(list(all_tickers))])
    else:
        formatted_tickers = "⚠️ <b>Тикеры не найдены</b>"
    formatted_date = date_match.group(1) if date_match else "См. анонс"
    formatted_time = time_match.group(1) if time_match else "См. анонс"
    
    return formatted_tickers, formatted_date, formatted_time

def parse_article_content(html_content, url):
    """
    Parses the HTML content of a delisting announcement to extract tickers, date, and time.
    """
    soup = BeautifulSoup(html_content, 'lxml')
    
    if "binance.com" in url:
        return _parse_binance_html(soup)
    elif "bybit.com" in url:
        return _parse_bybit_html(soup)
    else:
        logger.warning(f"Parser not implemented for URL: {url}")
        return "⚠️ <b>Тикеры не найдены</b>", "См. анонс", "См. анонс"

def format_delisting_message(exchange_name, tickers_str, date_str, time_str, url, is_test=False):
    """Formats a standardized delisting message for Telegram."""
    if is_test:
        header = f"🧪 <b>TEST {exchange_name.upper()} DELISTING</b> 🧪"
    else:
        header = f"🚨 <b>{exchange_name.upper()} DELISTING</b>"
        
    return (
        f"{header}\n\n"
        f"🪙 Монеты: {tickers_str}\n"
        f"📅 Дата: {date_str}\n"
        f"🕒 Время: {time_str}\n\n"
        f"🔗 <a href='{url}'>Читать анонс</a>"
    )

def get_processed_ids(state_file_name):
    """Load ID list of handled announcements in S3."""
    try:
        s3_object = s3_client.get_object(Bucket=BUCKET_NAME, Key=state_file_name)
        file_content = s3_object['Body'].read().decode('utf-8')
        # Handle empty file gracefully
        if not file_content:
            return []
        return json.loads(file_content)
    except s3_client.exceptions.NoSuchKey:
        logger.info(f"State file {state_file_name} not found. New file will be created.")
        return []
    except json.JSONDecodeError:
        logger.warning(f"State file {state_file_name} is empty or malformed. Starting fresh.")
        return []
    except Exception as error:
        logger.warning(f"State loading error from {state_file_name}: {error}")
        return []

def save_processed_ids(processed_ids, state_file_name):
    """Save ID list to S3."""
    try:
        s3_client.put_object(
            Bucket=BUCKET_NAME, 
            Key=state_file_name, 
            Body=json.dumps(processed_ids)
        )
    except Exception as error:
        logger.error(f"Error saving state to S3 in {state_file_name}: {error}")

def send_telegram_notification(message):
    """Send message to all predefined chats and topics."""
    if not BOT_TOKEN or not CHAT_IDS_STRING:
        logger.error("BOT_TOKEN or CHAT_IDS not found.")
        return
        
    try:
        chat_targets = json.loads(CHAT_IDS_STRING)
        if not isinstance(chat_targets, list):
            logger.error("CHAT_IDS is not a valid JSON list.")
            return
    except json.JSONDecodeError:
        logger.error("Failed to parse CHAT_IDS. Ensure it is a valid JSON string.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    for target in chat_targets:
        payload = {
            "text": message, 
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            if isinstance(target, (str, int)):
                payload['chat_id'] = target
            elif isinstance(target, dict) and 'chat_id' in target and 'message_thread_id' in target:
                payload['chat_id'] = target['chat_id']
                payload['message_thread_id'] = target['message_thread_id']
            else:
                logger.warning(f"Invalid target in CHAT_IDS: {target}")
                continue

            response = requests.post(url, json=payload, timeout=10)
            if not response.ok:
                logger.error(f"Telegram error for target {target}: {response.status_code} - {response.text}")
        except Exception as error:
            logger.error(f"Error sending Telegram message for target {target}: {error}")