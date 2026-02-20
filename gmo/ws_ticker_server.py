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


class ClientRegistry:
    def __init__(self):
        self._clients: set[ServerConnection] = set()
        self._lock = asyncio.Lock()

    async def add(self, client: ServerConnection) -> int:
        ...

    async def remove(self, client: ServerConnection):
        ...

    async def snapshot(self) -> list[ServerConnection]:
        ...

registry = ClientRegistry()

class LatestTickerCache:
    def __init__(self) -> None:
        self._ticker: dict | None = None
        self._lock = asyncio.Lock()

    async def set(self, payload: dict) -> None:
        ...

    async def get(self) -> dict | None:
        ...


latest_ticker = LatestTickerCache()



async def send_json(client: ServerConnection, payload: dict) -> None:
    try:
        await client.send(json.dumps(payload))
    except ConnectionClosed:
        pass

async def broadcast(payload) -> None:
    clients = await registry.snapshot()
    if not clients:
        return
    await asyncio.gather(*(send_json(client, payload) for client in clients), return_exceptions=True)

def normalize_ticker_record(row: tuple[datetime, float, float]) -> tuple[datetime, dict]:
    """
    DBのレコードをwebsocket用に整形する
    """
    ...

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

def fetch_rows_after(last_processed_time: datetime) -> list[tuple[datetime, float, float]]
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
    latest_row = await asyncio.to_thread(fetch_latest_row)
    last_processed_time = datetime(1970, 1,1,tzinfo=timezone.utc)


    # 処理済みの時刻以降のレコードを配信する











