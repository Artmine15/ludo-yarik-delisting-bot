import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.handlers.binance_handler import start_binance_websocket_listener # We'll refactor this handler soon

# This is a placeholder for the actual BinanceClient background task
# We will define a proper way to manage it soon.
_binance_task: asyncio.Task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Starting up FastAPI application...")
    
    # Start Binance WebSocket listener in the background
    # We create a task that runs in the event loop managed by FastAPI
    global _binance_task
    _binance_task = asyncio.create_task(start_binance_websocket_listener())
    
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

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Service is running"}

# You can add other API endpoints here if needed
