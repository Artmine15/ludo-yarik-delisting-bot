import uuid
import asyncio
import websockets
import json
from typing import Optional, Callable

# Public endpoint for general announcements (no API keys required for this stream)
BINANCE_WS_PUBLIC_BASE = "wss://://stream.binance.com"  # Corrected public endpoint
# Reconnection interval in seconds
RECONNECT_INTERVAL = 5
# PING interval is handled by websockets automatically; no explicit PING messages needed for public streams usually

class BinanceClient:
    def __init__(self, message_handler: Callable[[dict], None]):
        self.ws_base_url = BINANCE_WS_PUBLIC_BASE
        self.message_handler = message_handler
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._stop_event = asyncio.Event() # Event to signal stopping the client

    async def _send_subscription_request(self, websocket):
        """Подписка на поток объявлений в реальном времени."""
        request = {
            "method": "SUBSCRIBE",
            "params": [
                "!announcement" # Название нового потока объявлений
            ],
            "id": 1 # ID запроса может быть целым числом
        }
        await websocket.send(json.dumps(request))
        print(f"Подписка отправлена: {json.dumps(request)}")

    async def _listen_for_messages(self, websocket):
        async for message in websocket:
            msg_data = json.loads(message)
            # В новом потоке данные приходят с ключом "e": "announcement"
            if msg_data.get("e") == "announcement":
                print(f"Новое объявление: {msg_data.get('title')}")
                print(f"Ссылка: {msg_data.get('url')}")
            
            await asyncio.to_thread(self.message_handler, msg_data)

    async def connect_and_listen(self):
        """Establishes and maintains the WebSocket connection to Binance."""
        while not self._stop_event.is_set():
            try:
                print(f"Attempting to connect to public Binance WebSocket at {self.ws_base_url}...")
                async with websockets.connect(self.ws_base_url, ping_interval=20, ping_timeout=10) as websocket:
                    self._websocket = websocket
                    print("Successfully connected to Public Binance WebSocket.")
                    
                    # Send initial subscription request
                    await self._send_subscription_request(websocket)

                    # Listen for messages until connection closes or stop event is set
                    await self._listen_for_messages(websocket)

            except websockets.exceptions.ConnectionClosedOK:
                print("Connection closed cleanly, attempting to reconnect.")
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"Connection closed with error: {e}, attempting to reconnect.")
            except ConnectionRefusedError:
                print("Connection refused. Retrying...")
            except Exception as e:
                print(f"Unexpected error during WebSocket connection: {e}")
            finally:
                if self._websocket and not self._websocket.closed:
                    await self._websocket.close()
                if not self._stop_event.is_set():
                    print(f"Reconnecting in {RECONNECT_INTERVAL} seconds...")
                    await asyncio.sleep(RECONNECT_INTERVAL)
        print("BinanceClient stopped.")

    async def stop(self):
        """Signals the client to stop its operation."""
        self._stop_event.set()
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()
            print("Binance WebSocket connection explicitly closed.")