import asyncio
import json
import os
from datetime import datetime, timezone
import logging

from src.config.config import SCHEMA_NAME_TICKER
from src.database.base import session_scope
from sqlalchemy import text
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class StreamConfig:
    symbol: str
    table: str
    path: str

PATH_CONFIG_BY_PATH = {
    "/ws/ticker_usd_jpy": StreamConfig(
        symbol="USD_JPY",
        table="ticker_usd_jpy",
        path="/ws/ticker_usd_jpy",
    ),
    "/ws/ticker_eur_jpy": StreamConfig(
        symbol="EUR_JPY",
        table="ticker_eur_jpy",
        path="/ws/ticker_eur_jpy",
    ),
    "/ws/ticker_aud_jpy": StreamConfig(
        symbol="AUD_JPY",
        table="ticker_aud_jpy",
        path="/ws/ticker_aud_jpy",
    ),
    "/ws/ticker_chf_jpy": StreamConfig(
        symbol="CHF_JPY",
        table="ticker_chf_jpy",
        path="/ws/ticker_chf_jpy",
    ),
    "/ws/ticker_gbp_jpy": StreamConfig(
        symbol="GBP_JPY",
        table="ticker_gbp_jpy",
        path="/ws/ticker_gbp_jpy",
    ),
}


HEARTBEAT_INTERVAL_SECONDS = 30

DB_POLL_INTERVAL_SECONDS = float(os.getenv("DB_POLL_INTERVAL_SECONDS", "1.0"))
DB_ERROR_RETRY_SECONDS = 3

### helper methods ###
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

def normalize_utc_timestamp(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

#######################


### Class definition ###

class ClientRegistry:
    def __init__(self):
        self._clients: set[ServerConnection] = set()
        self._lock = asyncio.Lock()

    async def add(self, client: ServerConnection) -> int:
        async with self._lock:
            self._clients.add(client)

    async def remove(self, client: ServerConnection) -> int:
        async with self._lock:
            self._clients.discard(client)
            return len(self._clients)

    async def snapshot(self) -> list[ServerConnection]:
        async with self._lock:
            return list(self._clients)

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

#########################


### instances generation ###

# path毎にClientRegistryを作成する
registry_by_path: dict[str, ClientRegistry] = {
    path: ClientRegistry() for path in PATH_CONFIG_BY_PATH.keys()
}

# path毎にLatestTickerCacheを作成する
latest_ticker_by_path: dict[str, LatestTickerCache] = {
    path: LatestTickerCache() for path in PATH_CONFIG_BY_PATH.keys()
}

############################


### main functions ###

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
            "code": "INVALID PATH",
            "message": message,
            "timestamp": utc_now_iso(),
        },
    )
    await client.close(code=1008, reason=message)

async def broadcast_to_registry(registry: ClientRegistry, payload: dict):
    clients = await registry.snapshot()
    if not clients:
        return
    await asyncio.gather(*(send_json(client, payload) for client in clients), return_exceptions=True)

async def broadcast(payload) -> None:
    await asyncio.gather(
        *(broadcast_to_registry(registry, payload) for registry in registry_by_path.values()),
        return_exceptions=True
    )

def normalize_ticker_record(row: tuple[datetime, float, float], symbol: str) -> tuple[datetime, dict] | None:
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
                "symbol": symbol,
                "mid": mid,
            })


def fetch_latest_row(tablename: str) -> tuple[datetime, float, float] | None:
    """
    対象のテーブルから最新行を取得する
    """
    sql = text(
        f"""
        SELECT time, bid, ask
        FROM {SCHEMA_NAME_TICKER}.{tablename}
        ORDER BY time DESC
        LIMIT 1; 
        """
    )

    with session_scope() as session:
        row = session.execute(sql).first()
    return (row[0], row[1], row[2]) if row is not None else None

def fetch_rows_after(last_processed_time: datetime, tablename: str) -> list[tuple[datetime, float, float]]:
    """
    未処理のレコードを抽出する
    """
    sql = text(
        f"""
        SELECT time, bid, ask
        FROM {SCHEMA_NAME_TICKER}.{tablename}
        WHERE time > :last_time
        ORDER BY time;
        """
    )

    with session_scope() as session:
        rows = session.execute(sql, {"last_time": last_processed_time}).all()
    return [(row[0], row[1], row[2]) for row in rows]

async def db_relay_loop_by_path(path_config: StreamConfig):
    """
    通貨ペア毎に未処理の行を検出して、配信する
    """
    latest_cache = latest_ticker_by_path[path_config.path]
    registry = registry_by_path[path_config.path]

    # 初期化
    bootstrap_row = await asyncio.to_thread(fetch_latest_row, path_config.table)
    last_processed_time: datetime | None = None
    if bootstrap_row is not None:
        bootstrap_time = normalize_utc_timestamp(bootstrap_row[0])
        last_processed_time = bootstrap_time

        normalized_record = normalize_ticker_record(bootstrap_row, symbol=path_config.symbol)
        if normalized_record is not None:
            _, payload = normalized_record
            await latest_cache.set(payload)

    while True:
        try:
            rows = await asyncio.to_thread(fetch_rows_after, last_processed_time, path_config.table)
            for row in rows:
                current_time = normalize_utc_timestamp(row[0])
                normalized = normalize_ticker_record(row, symbol=path_config.symbol)
                if normalized is None:
                    last_processed_time = current_time
                    continue

                _, payload = normalized
                await latest_cache.set(payload)
                await broadcast_to_registry(registry, payload)
                last_processed_time = current_time

            await asyncio.sleep(DB_POLL_INTERVAL_SECONDS)

        except Exception:
            await broadcast_to_registry(
                registry,
                {
                    'type': 'error',
                    'code': 'DB_POLLING_FAILED',
                    'message': f'ticker db polling failed: {path_config.symbol}',
                    'timestamp': utc_now_iso(),
                }
            )
            await asyncio.sleep(DB_ERROR_RETRY_SECONDS)

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
    path_config = PATH_CONFIG_BY_PATH.get(path)
    if path_config is None:
        await send_error_and_close(client, f"unsupported path: {path}")
        return

    registry = registry_by_path.get(path)
    latest_ticker = latest_ticker_by_path.get(path)

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
    port = os.getenv("WS_PORT", 8765)

    async with serve(handler, host=host, port=port):
        relay_tasks = [db_relay_loop_by_path(config) for config in PATH_CONFIG_BY_PATH.values()]
        await asyncio.gather(
            heart_beat_loop(),
            *relay_tasks,
        )

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    asyncio.run(run_server())



















