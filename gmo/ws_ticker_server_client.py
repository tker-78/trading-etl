import asyncio, websockets

async def main():
    uri = "ws://0.0.0.0:8765/ws/ticker_usd_jpy"
    async with websockets.connect(uri) as ws:
        while True:
            print(await ws.recv())

if __name__ == "__main__":
    asyncio.run(main())
