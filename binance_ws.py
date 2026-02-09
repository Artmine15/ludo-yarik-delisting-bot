import asyncio
import json
import logging
import websockets
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from common import (
    parse_announcement_data,
    get_processed_ids,
    save_processed_ids,
    send_telegram_notification,
    logger
)

class TestNotification(BaseModel):
    title: str

app = FastAPI()

STATE_FILE = "binance_state.json"

@app.get("/health")
async def health_check():
    """Health check endpoint to ensure the service is running."""
    return {"status": "ok"}

@app.post("/test-notification")
async def test_notification(notification: TestNotification):
    """
    Receives a test title, formats a message, and sends it to Telegram.
    This is for manual end-to-end testing purposes.
    """
    logger.info(f"Received test notification with title: {notification.title}")
    
    tickers_str, date_str, time_str = parse_announcement_data(notification.title)
    
    message_to_send = (
        f"🧪 <b>TEST BINANCE DELISTING</b> 🧪\n\n"
        f"🪙 Монеты: {tickers_str}\n"
        f"📅 Дата: {date_str}\n"
        f"🕒 Время: {time_str}\n\n"
        f"🔗 <a href='https://www.binance.com/en/support/announcement/trading-pairs'>Читать анонс</a>"
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
                tickers_str, date_str, time_str = parse_announcement_data(title)
                
                message_to_send = (
                    f"🚨 <b>BINANCE DELISTING</b>\n\n"
                    f"🪙 Монеты: {tickers_str}\n"
                    f"📅 Дата: {date_str}\n"
                    f"🕒 Время: {time_str}\n\n"
                    f"🔗 <a href='{link}'>Читать анонс</a>"
                )
                
                send_telegram_notification(message_to_send)
                logger.info(f"Sent notification for {news_id}")

                processed_ids_list.append(news_id)
                processed_ids_set.add(news_id)
                
                updated_state = processed_ids_list[-50:]
                save_processed_ids(updated_state, STATE_FILE)
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
