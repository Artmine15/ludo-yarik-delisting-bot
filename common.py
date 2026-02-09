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
CHAT_IDS_STRING = os.getenv('CHAT_IDS', '')
CHAT_IDS = [chat_id.strip() for chat_id in CHAT_IDS_STRING.split(',') if chat_id.strip()]
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

    formatted_tickers = ', '.join(sorted(list(tickers))) if tickers else "⚠️ <b>Тикеры не найдены</b>"
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

    formatted_tickers = ', '.join(sorted(list(all_tickers))) if all_tickers else "⚠️ <b>Тикеры не найдены</b>"
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
    """Send message to all predefined chats."""
    if not BOT_TOKEN or not CHAT_IDS:
        logger.error("BOT_TOKEN or CHAT_IDS not found.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    for chat_id in CHAT_IDS:
        try:
            payload = {
                "chat_id": chat_id, 
                "text": message, 
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }
            response = requests.post(url, json=payload, timeout=10)
            if not response.ok:
                logger.error(f"Telegram error {response.status_code}: {response.text}")
        except Exception as error:
            logger.error(f"Error sending Telegram message in chat {chat_id}: {error}")
