import json
import websocket
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from database.base import session_scope
from database.base import Base
from sqlalchemy import Column, DateTime, Integer, String, Float

UTC = timezone.utc
JST = ZoneInfo('Asia/Tokyo')

class Streamer:
    if __debug__:
        websocket.enableTrace(True)

    def __init__(self):
        self.ws = websocket.WebSocketApp(
            'wss://forex-api.coin.z.com/ws/public/v1',
            on_open=self.on_open,
            on_message=self.on_message
        )

    def on_open(self, ws):
        message = {
            "command": "subscribe",
            "channel": "ticker",
            "symbol": "USD_JPY"
        }
        ws.send(json.dumps(message))

    def on_message(self, message, ws):
        data = json.loads(ws)
        # time = datetime.strptime(data['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')
        time = datetime.fromisoformat(data['timestamp'].replace("Z", "+00:00")).astimezone(UTC)
        bid = float(data['bid'])
        ask = float(data['ask'])
        print(time, bid, ask)
        Ticker.add_ticker(time, bid, ask)

    def run(self):
        self.ws.run_forever()

class Ticker(Base):
    __tablename__ = 'ticker_usd_jpy'
    __table_args__ = {"schema": "usd_jpy"}
    """
    Websocketから受信したデータを1sec単位で保存するためのオブジェクト
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
            record = session.query(Ticker).filter(Ticker.time == query_time)
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
            record = session.query(Ticker).filter(Ticker.time == truncated_time).count()
            if record == 0:
                ticker = Ticker(time=truncated_time, bid=bid, ask=ask)
                session.add(ticker)

    def truncate_in_sec(self) -> datetime:
        return self.time.replace(microsecond=0)

if __name__ == '__main__':
    Streamer().run()
    # Ticker.get_all()
