import asyncio
import json
import logging
import os
from datetime import datetime, timezone

from database.base import session_scope
from sqlalchemy import text
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed

WS_PATH = "/ws/ticker_usd_jpy"
HEARTBEAT_INTERVAL_SECONDS = 30
SYMBOL = "USD_JPY"
DB_POLL_INTERVAL_SECONDS = float(os.getenv("DB_POLL_INTERVAL_SECONDS", "1.0"))
DB_ERROR_RETRY_SECONDS = 3


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def normalize_utc_timestamp(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


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


class LatestTickerCache:
    def __init__(self) -> None:
        self._ticker: dict | None = None
        self._lock = asyncio.Lock()

    async def set(self, payload: dict) -> None:
        async with self._lock:
            self._ticker = dict(payload)

    async def get(self) -> dict | None:
        async with self._lock:
            return dict(self._ticker) if self._ticker is not None else None


latest_ticker = LatestTickerCache()


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


async def broadcast(payload: dict) -> None:
    clients = await registry.snapshot()
    if not clients:
        return
    await asyncio.gather(*(send_json(client, payload) for client in clients), return_exceptions=True)


def normalize_ticker_record(row: tuple[datetime, float, float]) -> tuple[datetime, dict] | None:
    record_time, bid_raw, ask_raw = row
    try:
        bid = float(bid_raw)
        ask = float(ask_raw)
        timestamp = normalize_utc_timestamp(record_time)
    except (TypeError, ValueError, AttributeError):
        return None

    if bid <= 0 or ask <= 0 or bid > ask:
        return None

    mid = (bid + ask) / 2
    return timestamp, {
        "type": "ticker",
        "symbol": SYMBOL,
        "bid": bid,
        "ask": ask,
        "mid": mid,
        "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
    }


def fetch_latest_row() -> tuple[datetime, float, float] | None:
    sql = text(
        """
        SELECT time, bid, ask
        FROM ticker_usd_jpy
        ORDER BY time DESC
        LIMIT 1
        """
    )
    with session_scope() as session:
        row = session.execute(sql).first()
    return None if row is None else (row[0], row[1], row[2])


def fetch_rows_after(last_processed_time: datetime) -> list[tuple[datetime, float, float]]:
    sql = text(
        """
        SELECT time, bid, ask
        FROM ticker_usd_jpy
        WHERE time > :last_time
        ORDER BY time ASC
        """
    )
    with session_scope() as session:
        rows = session.execute(sql, {"last_time": last_processed_time}).all()
    return [(row[0], row[1], row[2]) for row in rows]


async def db_relay_loop() -> None:
    logging.info("Starting DB polling relay interval=%.3fs", DB_POLL_INTERVAL_SECONDS)

    bootstrap_row = await asyncio.to_thread(fetch_latest_row)
    last_processed_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
    if bootstrap_row is not None:
        normalized = normalize_ticker_record(bootstrap_row)
        bootstrap_time = normalize_utc_timestamp(bootstrap_row[0])
        last_processed_time = bootstrap_time
        if normalized is not None:
            _, payload = normalized
            await latest_ticker.set(payload)
            logging.info("Bootstrapped latest ticker cache timestamp=%s", payload["timestamp"])

    while True:
        try:
            rows = await asyncio.to_thread(fetch_rows_after, last_processed_time)
            for row in rows:
                current_time = normalize_utc_timestamp(row[0])
                payload = normalize_ticker_record(row)
                if payload is None:
                    logging.warning("Skipping invalid ticker row time=%s bid=%s ask=%s", row[0], row[1], row[2])
                    last_processed_time = current_time
                    continue
                _, ticker_payload = payload
                await latest_ticker.set(ticker_payload)
                await broadcast(ticker_payload)
                last_processed_time = current_time
            await asyncio.sleep(DB_POLL_INTERVAL_SECONDS)
        except Exception:
            logging.exception("DB polling relay failed")
            await broadcast(
                {
                    "type": "error",
                    "code": "DB_POLLING_FAILED",
                    "message": "ticker db polling failed",
                    "timestamp": utc_now_iso(),
                }
            )
            await asyncio.sleep(DB_ERROR_RETRY_SECONDS)


async def heartbeat_loop() -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        payload = {"type": "heartbeat", "timestamp": utc_now_iso()}
        await broadcast(payload)


async def handler(client: ServerConnection) -> None:
    path = client.request.path
    if path != WS_PATH:
        logging.warning("Rejected client on invalid path: %s", path)
        await send_error_and_close(client, f"unsupported path: {path}")
        return

    connected = await registry.add(client)
    logging.info("Client connected path=%s total_connections=%d", path, connected)
    try:
        cached = await latest_ticker.get()
        if cached is not None:
            await send_json(client, cached)
        await client.wait_closed()
    finally:
        connected = await registry.remove(client)
        logging.info("Client disconnected path=%s total_connections=%d", path, connected)


async def run_server() -> None:
    host = os.getenv("WS_HOST", "0.0.0.0")
    port = int(os.getenv("WS_PORT", "8765"))
    logging.info("Starting ticker websocket server on ws://%s:%d%s", host, port, WS_PATH)

    async with serve(handler, host=host, port=port):
        await asyncio.gather(
            heartbeat_loop(),
            db_relay_loop(),
        )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    asyncio.run(run_server())
