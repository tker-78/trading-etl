import json
import os
import time
import websocket
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from database.base import session_scope
from database.base import Base
from sqlalchemy import Column, DateTime, Integer, String, Float, text

UTC = timezone.utc
JST = ZoneInfo('Asia/Tokyo')
SUBSCRIBE_INTERVAL_SECONDS = float(os.getenv("COINZ_SUBSCRIBE_INTERVAL_SECONDS", "1.0"))
RECONNECT_BACKOFF_SECONDS = float(os.getenv("COINZ_RECONNECT_BACKOFF_SECONDS", "5.0"))
RATE_LIMIT_ERROR = "ERR-5003 Request too many."

class Ticker(Base):
    __abstract__ = True
    """
    Websocketから受信したデータを1sec単位で保存するためのクラス
    """
    time = Column(DateTime, primary_key=True)
    bid = Column(Float)
    ask = Column(Float)

    def __init__(self, time: datetime, bid: float, ask: float):
        super().__init__()
        self.time = time
        self.bid = bid
        self.ask = ask

    @classmethod
    def get(cls, query_time: datetime):
        with session_scope() as session:
            record = session.query(cls).filter(cls.time == query_time)
            return record

    @classmethod
    def get_all(cls):
        with session_scope() as session:
            all_ticker = session.query(Ticker).all()
            print(all_ticker)
            return all_ticker

    @classmethod
    def add_ticker(cls, time: datetime, bid: float, ask: float):
        with session_scope() as session:
            truncated_time = cls(time, bid, ask).truncate_in_sec()
            record = session.query(cls).filter(cls.time == truncated_time).count()
            if record == 0:
                ticker = cls(time=truncated_time, bid=bid, ask=ask)
                session.add(ticker)

    def truncate_in_sec(self) -> datetime:
        return self.time.replace(microsecond=0)


# tickerオブジェクト生成ファクトリ
# dim_currencyからcurrency_pair_codeのリストを取得する
def get_currencies() -> list[str]:
    currency_list = []
    with session_scope() as session:
        query = text("""
        SELECT currency_pair_symbol
        FROM dim_currency;
        """)
        rows = session.execute(query)
        for row in rows:
            currency_list.append(row[0])
    return currency_list


# リストに基づきTickerクラスを生成するファクトリ
# currency_list = get_currencies()

class TickerUSDJPY(Ticker):
    __tablename__ = 'ticker_usd_jpy'
class TickerEURJPY(Ticker):
    __tablename__ = 'ticker_eur_jpy'
class TickerGBPJPY(Ticker):
    __tablename__ = 'ticker_gbp_jpy'
class TickerAUDJPY(Ticker):
    __tablename__ = 'ticker_aud_jpy'
class TickerNZDJPY(Ticker):
    __tablename__ = 'ticker_nzd_jpy'
class TickerCADJPY(Ticker):
    __tablename__ = 'ticker_cad_jpy'
class TickerCHFJPY(Ticker):
    __tablename__ = 'ticker_chf_jpy'

ticker_factory = {'USD_JPY': TickerUSDJPY, 'EUR_JPY': TickerEURJPY}
ticker_list = ticker_factory.keys()




class Streamer:
    if __debug__:
        websocket.enableTrace(True)

    def __init__(self, currency_pair_symbol):
        self.currency_pair_symbol = currency_pair_symbol
        self.rate_limit_hit = False
        self.ws = websocket.WebSocketApp(
            'wss://forex-api.coin.z.com/ws/public/v1',
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

    def on_open(self, ws):
        self.rate_limit_hit = False

        symbols = self.currency_pair_symbol
        if isinstance(symbols, str):
            symbols = [symbols]

        for symbol in symbols:
            message = {
                "command": "subscribe",
                "channel": "ticker",
                "symbol": symbol,
            }
            ws.send(json.dumps(message))
            # Avoid hitting subscribe rate limits when sending multiple requests.
            time.sleep(SUBSCRIBE_INTERVAL_SECONDS)

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            if data.get("error") == RATE_LIMIT_ERROR:
                self.rate_limit_hit = True
                print(
                    f"[{self.currency_pair_symbol}] rate limit hit: {data}. "
                    f"backing off {RECONNECT_BACKOFF_SECONDS}s before reconnect"
                )
                ws.close()
                return
            # Ignore non-ticker messages such as subscribe responses.
            if not all(k in data for k in ('symbol', 'timestamp', 'bid', 'ask')):
                print(f"[{self.currency_pair_symbol}] non-ticker message: {data}")
                return

            time = datetime.fromisoformat(data['timestamp'].replace("Z", "+00:00")).astimezone(UTC)
            bid = float(data['bid'])
            ask = float(data['ask'])
            symbol = data['symbol']
            print(symbol, time, bid, ask)

            ticker = ticker_factory.get(symbol)
            if ticker is None:
                print(f"unsupported symbol: {symbol}")
                return
            ticker.add_ticker(time, bid, ask)
        except Exception as e:
            print(f"[{self.currency_pair_symbol}] on_message error: {e}")
            raise

    def on_error(self, ws, error):
        print(f"[{self.currency_pair_symbol}] websocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print(f"[{self.currency_pair_symbol}] websocket closed: code={close_status_code}, msg={close_msg}")

    def run(self):
        while True:
            self.ws.run_forever()
            print(f"[{self.currency_pair_symbol}] reconnecting in {RECONNECT_BACKOFF_SECONDS}s")
            time.sleep(RECONNECT_BACKOFF_SECONDS)

if __name__ == '__main__':
    Streamer(ticker_list).run()
