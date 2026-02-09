import asyncio
import json
import logging
import requests
import websockets
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from common import (
    get_headers,
    parse_article_content,
    get_processed_ids,
    save_processed_ids,
    send_telegram_notification,
    format_delisting_message,
    logger
)

class TestPayload(BaseModel):
    html_content: str
    url: str

app = FastAPI()

STATE_FILE = "binance_state.json"

@app.get("/health")
async def health_check():
    """Health check endpoint to ensure the service is running."""
    return {"status": "ok"}

@app.post("/test-notification")
async def test_notification(payload: TestPayload):
    """
    Receives a test HTML content and URL, parses it, and sends a message.
    This is for manual end-to-end testing of the parser and notifier.
    """
    logger.info(f"Received test notification for URL: {payload.url}")
    
    tickers_str, date_str, time_str = parse_article_content(payload.html_content, payload.url)
    
    message_to_send = format_delisting_message(
        "BINANCE", tickers_str, date_str, time_str, payload.url, is_test=True
    )
    
    send_telegram_notification(message_to_send)
    
    return {"status": "test_notification_sent", "message": message_to_send}


def process_binance_message(data, processed_ids_list, processed_ids_set):
    """
    Processes a single message from the Binance WebSocket stream.
    This function is separate from the listener to allow for easier testing.
    """
    if 'data' in data and data.get('channel') == 'binance_announcements':
        announcement = data['data']
        title = announcement.get('article_title', '')
        link = announcement.get('article_url', '')
        article_id = announcement.get('article_id')
        
        keywords = ["delist", "removal", "cease", "trading pairs"]
        if any(word in title.lower() for word in keywords):
            news_id = f"binance_ws_{article_id}"

            if news_id not in processed_ids_set:
                try:
                    # Fetch article content
                    response = requests.get(link, headers=get_headers(), timeout=20)
                    if not response.ok:
                        logger.error(f"Failed to fetch Binance article {link}: Status {response.status_code}")
                        return

                    # Parse content to get details
                    tickers_str, date_str, time_str = parse_article_content(response.text, link)
                    
                    # Format and send message
                    message_to_send = format_delisting_message(
                        "BINANCE", tickers_str, date_str, time_str, link
                    )
                    
                    send_telegram_notification(message_to_send)
                    logger.info(f"Sent notification for {news_id}")

                    # Update state
                    processed_ids_list.append(news_id)
                    processed_ids_set.add(news_id)
                    
                    updated_state = processed_ids_list[-50:]
                    save_processed_ids(updated_state, STATE_FILE)

                except Exception as e:
                    logger.error(f"Error processing Binance announcement {link}: {e}")
            else:
                logger.info(f"Already processed announcement {news_id}")

async def binance_listener():
    """
    Connects to Binance WebSocket API and listens for delisting announcements.
    """
    url = "wss://ws-api.binance.com/ws-api/v3"
    subscribe_message = {
        "id": "1",
        "method": "c_subscribe",
        "params": {"channel": "binance_announcements"}
    }
    
    processed_ids_list = get_processed_ids(STATE_FILE)
    processed_ids_set = set(processed_ids_list)

    while True:
        try:
            async with websockets.connect(url) as websocket:
                await websocket.send(json.dumps(subscribe_message))
                logger.info("Subscribed to Binance announcements channel.")
                
                while True:
                    try:
                        message = await websocket.recv()
                        data = json.loads(message)
                        # Running synchronous code in an async context.
                        # For high-performance applications, consider using an async HTTP client (e.g., httpx)
                        # or running requests in a thread pool executor.
                        process_binance_message(data, processed_ids_list, processed_ids_set)

                    except websockets.exceptions.ConnectionClosed:
                        logger.warning("WebSocket connection closed. Reconnecting...")
                        break
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")

        except Exception as e:
            logger.error(f"Failed to connect to Binance WebSocket: {e}")
            await asyncio.sleep(60)

@app.on_event("startup")
async def startup_event():
    """
    On application startup, launch the binance_listener in the background.
    """
    logger.info("Starting Binance WebSocket listener as a background task.")
    asyncio.create_task(binance_listener())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    uvicorn.run(app, host="0.0.0.0", port=8000)
