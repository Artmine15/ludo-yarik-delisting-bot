import os
import json
import re
import logging
import boto3
import requests

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

def parse_announcement_data(title):
    """
    Parses the title to extract tickers, date, and time.
    Improved readability and reliability.
    """
    exclude_words = {
        'BINANCE', 'BYBIT', 'DELIST', 'DELISTING', 'LISTING', 'NOTICE', 
        'REMOVAL', 'SUPPORT', 'ANNOUNCEMENT', 'UTC', 'USDT', 'USDC', 
        'BTC', 'ETH', 'BUSD', 'FDUSD', 'SPOT', 'MARGIN', 'TOKEN'
    }
    
    clean_title = re.sub(r'[^\w\s]', ' ', title)
    raw_tickers = re.findall(r'\b[A-Z0-9]{2,10}\b', clean_title)
    
    tickers = []
    for word in raw_tickers:
        if word not in exclude_words and word not in tickers:
            tickers.append(word)
    
    date_pattern = r'(\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s\d{4}\b)'
    date_match = re.search(date_pattern, title, re.IGNORECASE)
    
    time_pattern = r'(\d{1,2}:\d{2}\s?(?:UTC)?)'
    time_match = re.search(time_pattern, title, re.IGNORECASE)
    
    formatted_tickers = f"{', '.join(tickers)}" if tickers else "⚠️ <b>Тикеры не найдены</b>"
    formatted_date = date_match.group(0) if date_match else "См. анонс"
    formatted_time = time_match.group(0) if time_match else "См. анонс"
    
    return formatted_tickers, formatted_date, formatted_time

def get_processed_ids(state_file_name):
    """Load ID list of handled announcements in S3."""
    try:
        s3_object = s3_client.get_object(Bucket=BUCKET_NAME, Key=state_file_name)
        file_content = s3_object['Body'].read().decode('utf-8')
        return json.loads(file_content)
    except s3_client.exceptions.NoSuchKey:
        logger.info(f"State file {state_file_name} not found. New file will be created.")
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
