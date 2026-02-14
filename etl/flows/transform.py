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


def update_rsi(connector,
                  period: int = 14,
                  currency_pair_code: str = "USD/JPY",
                  timeframe_code: str = "1m"):
    _calc_version = 0

    def ohlc_table():
        return f"{currency_pair_code.replace('/', '_').lower()}_{timeframe_code}"

    def _get_id() -> tuple[int, int]:
        currency_id_result = connector.execute(
            """
            SELECT id FROM dim_currency WHERE currency_pair_code = :currency_pair_code;
            """,
            {"currency_pair_code": currency_pair_code}
        )
        currency_id = currency_id_result.scalar()
        if currency_id is None:
            raise ValueError(f"Currency pair code {currency_pair_code} not found")

        timeframe_id_result = connector.execute(
            """
            SELECT id FROM dim_timeframe WHERE timeframe_code = :timeframe_code;
            """,
            {"timeframe_code": timeframe_code}
        )
        timeframe_id = timeframe_id_result.scalar()
        if timeframe_id is None:
            raise ValueError(f"Timeframe code {timeframe_code} not found")
        return currency_id, timeframe_id

    table_name = quoted_name(ohlc_table(), quote=True)

    currency_id, timeframe_id = _get_id()

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

    # rsi計算対象行をOHLCテーブルから取得する(time, closeのみ)
    # rsi計算に必要な行数を確保する。(対象行全体でNullが入らないようにするにはPeriod * 2のレコード数が必要)
    if latest_rsi_time:
        query = f"""
        WITH boundary AS (
        SELECT time
        FROM {table_name}
        WHERE time <= :latest_rsi_time
        ORDER BY time DESC
        OFFSET :period * 2 LIMIT 1
        )
        SELECT time, close
        FROM {table_name}
        WHERE time >= COALESCE((SELECT time FROM boundary), :latest_rsi_time)
        ORDER BY time;
        """

        query_result = connector.execute(query, {"period": period, "latest_rsi_time": latest_rsi_time})
    else:
        query = f"""
        SELECT time, close
        FROM {table_name}
        ORDER BY time;
        """
        query_result = connector.execute(query)

    rows = query_result.all()

    # talibでrsiを計算する
    closes = np.array([row[1] for row in rows], dtype=float)
    rsi_values = talib.RSI(closes, timeperiod=period)

    # for debug
    # values = { time: rsi_values for (time, close), rsi_values in zip(rows, rsi_values)}
    # print(values)

    # fact_rsiに計算結果をinsertする
    insert_rows = []

    for (time, close), rsi_value in zip(rows, rsi_values):
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

    print(insert_rows)

    insert_query = """
    INSERT INTO fact_rsi (time, currency_id, timeframe_id, period, calc_version, value)
    VALUES (:time, :currency_id, :timeframe_id, :period, :calc_version, :value)
    ON CONFLICT DO NOTHING;
    """
    connector.execute(insert_query, insert_rows)

def update_sma(connector,
               period: int = 14,
               currency_pair_code: str = "USD/JPY",
               timeframe_code: str = "1m"):

    _calc_version = 0

    table_name = quoted_name(ohlc_table(currency_pair_code, timeframe_code), quote=True)

    currency_id, timeframe_id = get_id(connector, currency_pair_code, timeframe_code)

    last_sma_result = connector.execute(
        f"""
        SELECT MAX(time)
        FROM fact_sma
        WHERE period = :period
        AND currency_id = :currency_id
        AND timeframe_id = :timeframe_id;
        """, {"period": period, "currency_id": currency_id, "timeframe_id": timeframe_id}
    )
    last_sma_time = last_sma_result.scalar()

    # 計算対象行を抽出する
    if last_sma_time:
        query = f"""
        WITH boundary AS (
        SELECT time
        FROM {table_name}
        WHERE time <= :last_sma_time
        ORDER BY time DESC
        OFFSET :period * 2 LIMIT 1
        )
        SELECT time, close
        FROM {table_name}
        WHERE time >= COALESCE((SELECT time FROM boundary), :last_sma_time)
        ORDER BY time;
        """
        query_result = connector.execute(query, {"period": period, "last_sma_time": last_sma_time})
    else:
        query = f"""
        SELECT time, close
        FROM {table_name}
        ORDER BY time;
        """
        query_result = connector.execute(query)

    rows = query_result.all()

    # talibでSMAを計算する
    closes = np.array([row[1] for row in rows ], dtype=float)
    sma_values = talib.SMA(closes, timeperiod=period)

    # fact_smaに計算結果をinsertする
    insert_rows = []

    for (time, close), sma_value in zip(rows, sma_values):
        insert_rows.append(
            {
                "time": time,
                "currency_id": currency_id,
                "timeframe_id": timeframe_id,
                "period": period,
                "calc_version": _calc_version,
                "value": float(sma_value),
            }
        )

    insert_query = """
    INSERT INTO fact_sma (time, currency_id, timeframe_id, period, calc_version, value)
    VALUES (:time, :currency_id, :timeframe_id, :period, :calc_version, :value)
    ON CONFLICT DO NOTHING;
    """
    connector.execute(insert_query, insert_rows)



def ohlc_table(currency_pair_code: str, timeframe_code: str):
    return f"{currency_pair_code.replace('/', '_').lower()}_{timeframe_code}"


def get_id(connector, currency_pair_code: str, timeframe_code: str) -> tuple[int, int]:
    currency_id_result = connector.execute(
        """
        SELECT id
        FROM dim_currency
        WHERE currency_pair_code = :currency_pair_code;
        """,
        {"currency_pair_code": currency_pair_code}
    )
    currency_id = currency_id_result.scalar()
    if currency_id is None:
        raise ValueError(f"Currency pair code {currency_pair_code} not found")

    timeframe_id_result = connector.execute(
        """
        SELECT id
        FROM dim_timeframe
        WHERE timeframe_code = :timeframe_code;
        """,
        {"timeframe_code": timeframe_code}
    )
    timeframe_id = timeframe_id_result.scalar()
    if timeframe_id is None:
        raise ValueError(f"Timeframe code {timeframe_code} not found")
    return currency_id, timeframe_id


def insert_sma_golden_cross(connector):
    query = """
    WITH sma AS (
    SELECT
      s.time,
      s.currency_id,
      s.timeframe_id,
      s.calc_version,
      s.value AS short_value,
      l.value AS long_value
    FROM fact_sma s
    JOIN fact_sma l
      ON s.time = l.time
     AND s.currency_id = l.currency_id
     AND s.timeframe_id = l.timeframe_id
     AND s.calc_version = l.calc_version
    WHERE s.period = :short_period
      AND l.period = :long_period
  ),
  flag AS (
    SELECT
      *,
      LAG(short_value) OVER (
        PARTITION BY currency_id, timeframe_id, calc_version
        ORDER BY time
      ) AS prev_short,
      LAG(long_value) OVER (
        PARTITION BY currency_id, timeframe_id, calc_version
        ORDER BY time
      ) AS prev_long
    FROM sma
  )
  SELECT
    time, currency_id, timeframe_id, calc_version,
    short_value, long_value
  FROM flag
  WHERE prev_short <= prev_long
    AND short_value > long_value;
    
    """

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
        # update_rsi(conn)
        # update_rsi(conn, timeframe_code="5m")
        update_rsi(conn, timeframe_code="1m")
        update_rsi(conn, timeframe_code="5m")
        update_rsi(conn, timeframe_code="30m")
        update_rsi(conn, timeframe_code="1h")
        update_rsi(conn, timeframe_code="4h")
        update_sma(conn)


if __name__ == "__main__":
    transform()
    indicator()