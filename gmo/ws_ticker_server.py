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

def normalize_utc_timestamp(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class ClientRegistry:
    def __init__(self):
        self._clients: set[ServerConnection] = set()
        self._lock = asyncio.Lock()

    async def add(self, client: ServerConnection) -> int:
        async with self._lock:
            self._clients.add(client)

    async def remove(self, client: ServerConnection):
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

async def send_error_and_close(client: ServerConnection):
    ...

async def broadcast(payload) -> None:
    clients = await registry.snapshot()
    if not clients:
        return
    await asyncio.gather(*(send_json(client, payload) for client in clients), return_exceptions=True)

def normalize_ticker_record(row: tuple[datetime, float, float]) -> tuple[datetime, dict] | None:
    """
    DBのレコードをwebsocket用に整形する
    """
    record_time, bid_row, ask_row = row
    try:
        bid = float(bid_row)
        ask = float(ask_row)
        timestamp = normalize_utc_timestamp(record_time)
    except (TypeError, ValueError, AttributeError):
        return None

    mid = (bid + ask) / 2
    return (timestamp,
            {
                "bid": bid,
                "ask": ask,
                "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "type": "ticker",
                "symbol": SYMBOL,
                "mid": mid,
            })


def fetch_latest_row() -> tuple[datetime, float, float] | None:
    """
    対象のテーブルから最新行を取得する
    """
    sql = text(
        """
        SELECT time, bid, ask
        FROM ticker_usd_jpy
        ORDER BY time DESC
        LIMIT 1; 
        """
    )

    with session_scope() as session:
        row = session.execute(sql).first()
    return (row[0], row[1], row[2]) if row is not None else None

def fetch_rows_after(last_processed_time: datetime) -> list[tuple[datetime, float, float]]:
    """
    未処理のレコードを抽出する
    """
    sql = text(
        """
        SELECT time, bid, ask
        FROM ticker_usd_jpy
        WHERE time > :last_time
        ORDER BY time;
        """
    )

    with session_scope() as session:
        rows = session.execute(sql, {"last_time": last_processed_time}).all()
    return [(row[0], row[1], row[2]) for row in rows]


async def db_relay_loop() -> None:
    """
    未処理の行を検出して、配信する
    """

    # 処理済みの時刻を割り出す
    bootstrap_row = await asyncio.to_thread(fetch_latest_row)
    last_processed_time = None
    if bootstrap_row is not None:
        normalized_record = normalize_ticker_record(bootstrap_row)
        bootstrap_time = normalize_utc_timestamp(bootstrap_row[0])
        last_processed_time = bootstrap_time

        if normalized_record is not None:
            _, payload = normalized_record
            await latest_ticker.set(payload)

    # 処理済みの時刻以降のレコードを配信する
    while True:
        try:
            rows = await asyncio.to_thread(fetch_rows_after, last_processed_time)
            for row in rows:
                current_time = normalize_utc_timestamp(row[0])
                payload = normalize_ticker_record(row)
                if payload is None:
                    last_processed_time = current_time
                    continue
                _, ticker_payload = payload
                await latest_ticker.set(ticker_payload)
                await broadcast(ticker_payload)
                last_processed_time = current_time
            await asyncio.sleep(DB_POLL_INTERVAL_SECONDS)
        except Exception:
            await broadcast(
                {
                    "type": "error",
                    "code": "DB_POLLING_FAILED",
                    "message": "ticker db polling failed",
                    "timestamp": utc_now_iso(),
                }
            )
            await asyncio.sleep(DB_POLL_INTERVAL_SECONDS)

async def heart_beat_loop():
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        payload = {"type": "heartbeat", "timestamp": utc_now_iso()}
        await broadcast(payload)


async def handler(client: ServerConnection) -> None:
    """
    registry, TickerCacheの制御
    """
    # ws以外の接続を拒否する
    path = client.request.path
    if path != WS_PATH:
        await send_error_and_close(client, f"unsupported path: {path}")
        return

    # clientの処理
    connected = await registry.add(client)
    try:
        cached = await latest_ticker.get()
        if cached is not None:
            await send_json(client, cached)
        await client.wait_closed()
    finally:
        connected = await registry.remove(client)

async def run_server() -> None:
    host = os.getenv("WS_HOST", "0.0.0.0")
    port = os.getenv("WS_PORT", "8765")

    async with serve(handler, host=host, port=port):
        await asyncio.gather(
            heart_beat_loop(),
            db_relay_loop(),
        )

if __name__ == "__main__":
    asyncio.run(run_server())



















