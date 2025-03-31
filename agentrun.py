import asyncio
import websockets

async def receive_logs():
    uri = "ws://localhost:8002/ws"
    async with websockets.connect(uri) as websocket:
        print("Connected to WebSocket...")
        while True:
            response = await websocket.recv()
            print("\n🔹 AI Analysis Received:\n", response)

asyncio.run(receive_logs())