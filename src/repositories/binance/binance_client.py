import asyncio
import websockets
import json
from typing import Optional, Callable
# from datetime import datetime # No longer needed as _get_timestamp is removed

# Публичный эндпоинт с портом для стабильности
BINANCE_WS_PUBLIC_BASE = "wss://stream.binance.com:9443/ws"
RECONNECT_INTERVAL = 5

class BinanceClient:
    def __init__(self, message_handler: Callable[[dict], None]): # Corrected from init to __init__
        self.ws_base_url = BINANCE_WS_PUBLIC_BASE
        self.message_handler = message_handler
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._stop_event = asyncio.Event() 

    async def _send_subscription_request(self, websocket):
        """Подписка на поток объявлений."""
        request = {
            "method": "SUBSCRIBE",
            "params": [
                "!announcement" 
            ],
            "id": 1
        }
        await websocket.send(json.dumps(request))
        print(f"Подписка отправлена: {json.dumps(request)}")

    # def _get_timestamp(self): # Removed as it's not used after refactoring _listen_for_messages
    #     return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    async def _listen_for_messages(self, websocket):
        async for message in websocket:
            msg_data = json.loads(message)
            
            # Adapt message format for the existing message_handler
            if msg_data.get("e") == "announcement":
                # Translate new keys 't' and 'u' to 'title' and 'url'
                # Create a mutable copy to add new keys
                processed_msg_data = msg_data.copy()
                processed_msg_data["title"] = msg_data.get('t', '')
                processed_msg_data["url"] = msg_data.get('u', '')
                
                # Pass the adapted message to the handler
                if self.message_handler:
                    if asyncio.iscoroutinefunction(self.message_handler):
                        await self.message_handler(processed_msg_data)
                    else:
                        await asyncio.to_thread(self.message_handler, processed_msg_data)
            else:
                # For non-announcement messages, pass as is
                if self.message_handler:
                    if asyncio.iscoroutinefunction(self.message_handler):
                        await self.message_handler(msg_data)
                    else:
                        await asyncio.to_thread(self.message_handler, msg_data)

    async def connect_and_listen(self):
        """Установка и поддержание соединения (из твоего исходника)."""
        while not self._stop_event.is_set():
            try:
                print(f"Попытка подключения к {self.ws_base_url}...")
                async with websockets.connect(
                    self.ws_base_url, 
                    ping_interval=20, 
                    ping_timeout=10
                ) as websocket:
                    self._websocket = websocket
                    print("✅ Соединение установлено.")
                    
                    await self._send_subscription_request(websocket)
                    await self._listen_for_messages(websocket)

            except websockets.exceptions.ConnectionClosedOK:
                print("Соединение закрыто чисто (OK), переподключение...")
            except Exception as e:
                print(f"Ошибка WebSocket: {e}")
            finally:
                if self._websocket and not self._websocket.closed:
                    await self._websocket.close()
                if not self._stop_event.is_set():
                    print(f"Реконнект через {RECONNECT_INTERVAL} сек...")
                    await asyncio.sleep(RECONNECT_INTERVAL)

    async def stop(self):
        """Остановка клиента."""
        self._stop_event.set()
        if self._websocket and not self._websocket.closed:
            await self._websocket.close()
            print("Соединение Binance закрыто вручную.")

            