import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.handlers.binance_handler import start_binance_websocket_listener, process_binance_websocket_message
from src.repositories.binance.binance_client import BinanceClient

# This is a placeholder for the actual BinanceClient background task
# We will define a proper way to manage it soon.
_binance_task: asyncio.Task = None
_binance_client: BinanceClient = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting up FastAPI application...")
    
    # Initialize BinanceClient
    global _binance_client
    _binance_client = BinanceClient(message_handler=process_binance_websocket_message)

    # Start Binance WebSocket listener in the background
    # We create a task that runs in the event loop managed by FastAPI
    global _binance_task
    _binance_task = asyncio.create_task(start_binance_websocket_listener(client_instance=_binance_client))
    
    yield
    
    # Shutdown logic
    print("Shutting down FastAPI application...")
    if _binance_task:
        _binance_task.cancel() # Request cancellation
        try:
            await _binance_task # Await for the task to finish cancelling
        except asyncio.CancelledError:
            print("Binance WebSocket listener task cancelled.")
        except Exception as e:
            print(f"Error during Binance WebSocket listener shutdown: {e}")
    
    if _binance_client:
        await _binance_client.stop()

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}

# You can add other API endpoints here if needed
