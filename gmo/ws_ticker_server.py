import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

WS_PATH = "/ws/ticker_usd_jpy"
HEARTBEAT_INTERVAL_SECONDS = 30


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ClientRegistry:
    def __init__(self) -> None:
        self._clients: set[ServerConnection] = set()
        self._lock = asyncio.Lock()

    async def add(self, client: ServerConnection) -> int:
        async with self._lock:
            self._clients.add(client)
            return len(self._clients)

    async def remove(self, client: ServerConnection) -> int:
        async with self._lock:
            self._clients.discard(client)
            return len(self._clients)

    async def snapshot(self) -> list[ServerConnection]:
        async with self._lock:
            return list(self._clients)


registry = ClientRegistry()


async def send_json(client: ServerConnection, payload: dict) -> None:
    try:
        await client.send(json.dumps(payload))
    except ConnectionClosed:
        pass


async def send_error_and_close(client: ServerConnection, message: str) -> None:
    await send_json(
        client,
        {
            "type": "error",
            "code": "INVALID_PATH",
            "message": message,
            "timestamp": utc_now_iso(),
        },
    )
    await client.close(code=1008, reason=message)


async def heartbeat_loop() -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        clients = await registry.snapshot()
        if not clients:
            continue

        payload = {"type": "heartbeat", "timestamp": utc_now_iso()}
        await asyncio.gather(*(send_json(client, payload) for client in clients), return_exceptions=True)


async def handler(client: ServerConnection) -> None:
    path = client.request.path
    if path != WS_PATH:
        logging.warning("Rejected client on invalid path: %s", path)
        await send_error_and_close(client, f"unsupported path: {path}")
        return

    connected = await registry.add(client)
    logging.info("Client connected path=%s total_connections=%d", path, connected)
    try:
        await client.wait_closed()
    finally:
        connected = await registry.remove(client)
        logging.info("Client disconnected path=%s total_connections=%d", path, connected)


async def run_server() -> None:
    host = os.getenv("WS_HOST", "0.0.0.0")
    port = int(os.getenv("WS_PORT", "8765"))
    logging.info("Starting ticker websocket server on ws://%s:%d%s", host, port, WS_PATH)

    async with serve(handler, host=host, port=port):
        await heartbeat_loop()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    asyncio.run(run_server())
