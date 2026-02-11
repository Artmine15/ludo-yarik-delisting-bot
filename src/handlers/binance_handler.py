import asyncio
from src.repositories.binance.binance_client import BinanceClient
from src.bot.output_message_sender import OutputMessageSender
from src.utils.binance.binance_parser import parse_announcement_title
from src.utils.output_message_formatter import format_delisting_message

# Define delisting keywords
DELISTING_KEYWORDS = ["delist", "removal", "remove", "suspend trading", "discontinue"]

# This function will be called by the BinanceClient when a new message is received
def process_binance_websocket_message(message: dict):
    # Initialize sender here to avoid passing it around or making it global
    output_sender = OutputMessageSender() 

    # Filter for announcement events
    if message.get("e") == "announcement":
        title = message.get("title", "")
        article_url = message.get("url", "")
        
        # Check for delisting keywords in the title (case-insensitive)
        is_delisting_announcement = any(keyword in title.lower() for keyword in DELISTING_KEYWORDS)

        if is_delisting_announcement:
            print(f"DELISTING ANNOUNCEMENT DETECTED: {title}")
            
            # Parse the title to extract tickers, date, and time
            parsed_data = parse_announcement_title(title)
            
            # Format the message for Telegram
            formatted_telegram_message = format_delisting_message(
                header="BINANCE",
                tickers=parsed_data.get("tickers"),
                date=parsed_data.get("date"),
                time=parsed_data.get("time"),
                announcement_url=article_url
            )
            
            # Send the formatted message to Telegram
            output_sender.send_telegram_message(formatted_telegram_message)
        else:
            print(f"BINANCE ANNOUNCEMENT (non-delisting): {title}")

async def start_binance_websocket_listener(client_instance: BinanceClient):
    """
    Starts the Binance WebSocket client's connection and listening loop.
    This function is intended to be run as an asyncio task within a larger application.
    """
    print("Binance WebSocket listener task started.")
    await client_instance.connect_and_listen()
    print("Binance WebSocket listener task stopped.")

# The _binance_client instance will be created and managed by the main FastAPI app.
