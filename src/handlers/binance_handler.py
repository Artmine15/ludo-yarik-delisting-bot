import asyncio
from src.repositories.binance.binance_client import BinanceClient
from src.bot.output_message_sender import OutputMessageSender

# This function will be called by the BinanceClient when a new message is received
def process_binance_websocket_message(message: dict):
    # For now, just print the message.
    # Later, this is where we'll implement parsing, formatting, and sending to Telegram.
    print(f"HANDLER RECEIVED BINANCE MESSAGE: {message}")
    
    # Example of forwarding to Telegram (simplified for now)
    # output_sender = OutputMessageSender()
    # if message.get("e") == "announcement":
    #     title = message.get("title", "No Title")
    #     asyncio.run(output_sender.send_telegram_message(f"Binance Announcement: {title}"))


def start_binance_websocket_listener():
    """
    Main entry point to start the Binance WebSocket client.
    This function should be called to run the WebSocket listener as a long-running process.
    """
    print("Initializing Binance WebSocket client...")
    # Instantiate BinanceClient with our message processing function
    binance_client = BinanceClient(message_handler=process_binance_websocket_message)
    
    # Run the client's connection and listening loop
    # asyncio.run() manages the event loop for us
    asyncio.run(binance_client.connect_and_listen())

# This block allows the script to be run directly for testing/deployment
if __name__ == "__main__":
    start_binance_websocket_listener()