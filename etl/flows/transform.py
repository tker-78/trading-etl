from prefect import flow
import numpy as np
import talib
from prefect_sqlalchemy import SqlAlchemyConnector
from sqlalchemy.sql.elements import quoted_name
from decimal import Decimal, ROUND_HALF_UP

def update_usd_jpy_1m(connector):
    query = """
INSERT INTO usd_jpy_1m (time, open, high, low, close)
WITH bucket_time AS (
SELECT
    DATE_TRUNC('minute', time) AS bucket,
    time,
    bid
FROM ticker_usd_jpy
)
SELECT
bucket AS time,
(array_agg(bid ORDER BY time))[1] AS open,
MAX(bid) AS high,
MIN(bid) AS low,
(array_agg(bid ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;
    """
    connector.execute(query)

def update_usd_jpy_5m(connector):
    query = """
INSERT INTO usd_jpy_5m (time, open, high, low, close)
WITH bucket_time AS (
SELECT
    date_trunc('minute', time) - (EXTRACT(minute FROM time)::int % 5) * interval  '1 minute' AS bucket,
    time,
    open,
    high,
    low,
    close
FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY bucket))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;    
    """
    connector.execute(query)

def update_usd_jpy_30m(connector):
    query = """
INSERT INTO usd_jpy_30m (time, open, high, low, close)
WITH bucket_time AS (
SELECT
    date_trunc('minute', time) - (EXTRACT(minute FROM time)::int % 30) * interval  '1 minute' AS bucket,
    time,
    open,
    high,
    low,
    close
FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY bucket))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;
    """
    connector.execute(query)

def update_usd_jpy_1h(connector):
    query = """
INSERT INTO usd_jpy_1h (time, open, high, low, close)
WITH bucket_time AS (
    SELECT
        date_trunc('hour', time) AS bucket,
        time,
        open,
        high,
        low,
        close
    FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY time))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;
    """
    connector.execute(query)

def update_usd_jpy_4h(connector):
    query = """
INSERT INTO usd_jpy_4h (time, open, high, low, close)
WITH bucket_time AS (
    SELECT
        date_trunc('hour', time) - (EXTRACT(hour FROM time)::int % 4) * interval '1 hour' AS bucket,
        time,
        open,
        high,
        low,
        close
    FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY time))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;
    """
    connector.execute(query)



def update_rsi(connector, period: int = 14, currency_pair_code: str = "USD/JPY",  timeframe_code: str = "1m" ):
    _calc_version = 1

    def ohlc_table():
        return f"{currency_pair_code.replace('/', '_').lower()}_{timeframe_code}"

    # periodのValidation
    if not isinstance(period, int) or period < 2:
        raise ValueError("period must be an integer >= 2")

    # currency_idの取得
    currency_id_result = connector.execute(
        """
        SELECT id FROM dim_currency WHERE currency_pair_code = :currency_pair_code;
        """,
        {"currency_pair_code":  currency_pair_code}
    )
    currency_id = currency_id_result.scalar()

    if currency_id is None:
        raise ValueError(f"Currency pair code {currency_pair_code} not found")
    print("currency_id: ", currency_id)

    # timeframe_idの取得
    timeframe_id_result = connector.execute(
        """
        SELECT id FROM dim_timeframe WHERE timeframe_code = :timeframe_code;
        """,
        {"timeframe_code": timeframe_code}
    )
    timeframe_id = timeframe_id_result.scalar()
    if timeframe_id is None:
        raise ValueError(f"Timeframe code {timeframe_code} not found")
    print("timeframe_id: ", timeframe_id)

    # table_nameの取得
    table_name = quoted_name(ohlc_table(), quote=True)

    # fact_rsiの最新行を取得する
    latest_rsi_result = connector.execute(
        """
        SELECT MAX(time) 
        FROM fact_rsi 
        WHERE period = :period
            AND currency_id = :currency_id
            AND timeframe_id = :timeframe_id;
        """,
        {"period": period, "currency_id": currency_id, "timeframe_id": timeframe_id}
    )
    latest_rsi_time = latest_rsi_result.scalar()
    print("latest_rsi_time: ", latest_rsi_time)

    # RSI計算対象行をOHLCテーブルから取得する
    if latest_rsi_time:
        query = f"""
        WITH boundary AS (
            SELECT time
            FROM {table_name}
            WHERE time <= :latest_rsi_time
            ORDER BY time DESC
            OFFSET :period + 100 LIMIT 1
        )
        SELECT time, close
        FROM {table_name}
        WHERE time >= COALESCE((SELECT time FROM boundary), :latest_rsi_time)
        ORDER BY time;
        """
        rows_result = connector.execute(
            query,
            {"latest_rsi_time": latest_rsi_time, "period": period }
        )
    else:
        query = f"""
            SELECT time, close FROM {table_name} ORDER BY time;
            """
        rows_result = connector.execute(query)

    rows = rows_result.all()
    print("rows: ", rows)



    # talibでRSIを計算する
    closes = np.array([row[1] for row in rows], dtype=float)
    print("closes: ", closes)
    rsi_values = talib.RSI(closes, timeperiod=period)
    print("rsi_values: ", rsi_values)


    # fact_rsiに計算結果をInsertする
    insert_rows = []

    for (time, close), rsi_value in zip(rows, rsi_values):
        # precise_value = Decimal(str(rsi_value)).quantize(Decimal("0.0000"))
        insert_rows.append(
            {
                "time": time,
                "currency_id": currency_id,
                "timeframe_id": timeframe_id,
                "calc_version": _calc_version,
                "period": period,
                "value": float(rsi_value),
            }
        )

    insert_query = """
INSERT INTO fact_rsi (time, currency_id, timeframe_id, period, calc_version, value)
VALUES 
(:time, :currency_id, :timeframe_id, :period, :calc_version, :value)
ON CONFLICT DO NOTHING;
    """
    connector.execute(insert_query, insert_rows)


@flow
def transform(block_name: str = "forex-connector"):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_usd_jpy_1m(conn)
        update_usd_jpy_5m(conn)
        update_usd_jpy_30m(conn)
        update_usd_jpy_1h(conn)
        update_usd_jpy_4h(conn)

@flow
def indicator(block_name: str = "forex-connector"):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_rsi(conn)
        update_rsi(conn, timeframe_code="5m")


if __name__ == "__main__":
    transform()
    indicator()
