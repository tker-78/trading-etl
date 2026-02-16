from prefect import flow, task
import numpy as np
import talib
from prefect_sqlalchemy import SqlAlchemyConnector
from sqlalchemy.sql.elements import quoted_name
from etl.flows.config import *


##### helpers: start ########
def _ohlc_table(currency_pair_code: str, timeframe_code: str):
    return f"{currency_pair_code.replace('/', '_').lower()}_{timeframe_code}"

def _get_ids(connector, currency_pair_code: str, timeframe_code: str) -> tuple[int, int]:
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

def _build_rsi_params(overrides: dict | None = None) -> dict:
    return {**RSI_TASK_DEFAULT_PARAMS, **(overrides or {})}

def _build_sma_params(overrides: dict | None = None) -> dict:
    return {**SMA_TASK_DEFAULT_PARAMS, **(overrides or {})}

def _build_sma_golden_cross_params(overrides: dict | None = None) -> dict:
    return {**SMA_GOLDEN_CROSS_PARAMS, **(overrides or {})}

def _build_sma_dead_cross_params(overrides: dict | None = None) -> dict:
    return {**SMA_DEAD_CROSS_PARAMS, **(overrides or {})}

def _build_ema_params(overrides: dict | None = None) -> dict:
    return {**EMA_TASK_DEFAULT_PARAMS, **(overrides or {})}

##### helpers: end ########


######### update OHLC tables ##############

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

######### update OHLC tables: end ##############



######## update indicators: start #############




def update_rsi(connector,
               *,
               period: int,
               currency_pair_code: str,
               timeframe_code: str
               ):
    _calc_version = 0

    table_name = quoted_name(_ohlc_table(currency_pair_code, timeframe_code), quote=True)

    currency_id, timeframe_id = _get_ids(connector, currency_pair_code, timeframe_code)

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

    insert_query = """
    INSERT INTO fact_rsi (time, currency_id, timeframe_id, period, calc_version, value)
    VALUES (:time, :currency_id, :timeframe_id, :period, :calc_version, :value)
    ON CONFLICT DO NOTHING;
    """
    connector.execute(insert_query, insert_rows)

def update_sma(connector,
               *,
               period: int,
               currency_pair_code: str,
               timeframe_code: str
               ):

    _calc_version = 0

    table_name = quoted_name(_ohlc_table(currency_pair_code, timeframe_code), quote=True)

    currency_id, timeframe_id = _get_ids(connector, currency_pair_code, timeframe_code)

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

def update_ema(connector,
               *,
               period: int,
               currency_pair_code: str,
               timeframe_code: str
               ):

    _calc_version = 0

    table_name = quoted_name(_ohlc_table(currency_pair_code, timeframe_code), quote=True)

    currency_id, timeframe_id = _get_ids(connector, currency_pair_code, timeframe_code)

    last_ema_result = connector.execute(
        f"""
        SELECT MAX(time)
        FROM fact_ema
        WHERE period = :period
        AND currency_id = :currency_id
        AND timeframe_id = :timeframe_id;
        """, {"period": period, "currency_id": currency_id, "timeframe_id": timeframe_id}
    )

    last_ema_time = last_ema_result.scalar()

    # 計算対象行を抽出する
    if last_ema_time:
        query = f"""
        WITH boundary AS (
        SELECT time
        FROM {table_name}
        WHERE time <= :last_ema_time
        ORDER BY time DESC
        OFFSET :period * 2 LIMIT 1
        )
        SELECT time, close
        FROM {table_name}
        WHERE time >= COALESCE((SELECT time FROM boundary), :last_ema_time)
        ORDER BY time;
        """
        query_result = connector.execute(query, {"period": period, "last_ema_time": last_ema_time})
    else:
        query = f"""
        SELECT time, close
        FROM {table_name}
        ORDER BY time;
        """
        query_result = connector.execute(query)

    rows = query_result.all()

    # talibでemaを計算する
    closes = np.array([row[1] for row in rows], dtype=float)
    ema_values = talib.EMA(closes, timeperiod=period)

    # fact_emaに計算結果をinsertする
    insert_rows = []

    for (time, close), ema_value in zip(rows, ema_values):
        insert_rows.append(
            {
                "time": time,
                "currency_id": currency_id,
                "timeframe_id": timeframe_id,
                "period": period,
                "calc_version": _calc_version,
                "value": float(ema_value),
            }
        )

    insert_query = f"""
    INSERT INTO fact_ema (time, currency_id, timeframe_id, period, calc_version, value)
    VALUES (:time, :currency_id, :timeframe_id, :period, :calc_version, :value)
    ON CONFLICT DO NOTHING;
    """
    connector.execute(insert_query, insert_rows)


######## update indicators: end #############



######## insert signals based on a strategy: start #############

def insert_sma_golden_cross(connector,
                            *,
                            short_period: int,
                            long_period: int,
                            # currency_pair_code: str,
                            # timeframe_code: str
):
    # **todo**
    # timeframeを指定する
    query = """
    INSERT INTO fact_buysell_events (
        event_datetime, 
        currency_id, 
        price, 
        quantity, 
        event_type, 
        trigger_indicator_name, 
        trigger_indicator_value, 
        trigger_indicator_timeframe, 
        trigger_indicator_period
    )
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
    time, 
    currency_id, 
    short_value AS price, 
    0 AS quantity,
    'BUY' AS event_type, 
    'SMA' AS trigger_indicator_name,
    short_value AS trigger_indicator_value, 
    timeframe_id AS trigger_indicator_timeframe, 
    :short_period AS trigger_indicator_period
  FROM flag
  WHERE prev_short <= prev_long
    AND short_value > long_value
  ON CONFLICT DO NOTHING;

    """
    connector.execute(query, {"short_period": short_period, "long_period": long_period})


def insert_sma_dead_cross(connector,*, short_period: int, long_period: int):
    query = f"""
    INSERT INTO fact_buysell_events (
        event_datetime, 
        currency_id, 
        price, 
        quantity, 
        event_type, 
        trigger_indicator_name, 
        trigger_indicator_value, 
        trigger_indicator_timeframe, 
        trigger_indicator_period
    )
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
    time, 
    currency_id, 
    short_value AS price, 
    0 AS quantity,
    'SELL' AS event_type, 
    'SMA' AS trigger_indicator_name,
    short_value AS trigger_indicator_value, 
    timeframe_id AS trigger_indicator_timeframe, 
    :short_period AS trigger_indicator_period
  FROM flag
  WHERE prev_short >= prev_long
    AND short_value < long_value
  ON CONFLICT DO NOTHING;
"""
    connector.execute(query, {"short_period": short_period, "long_period": long_period})

######## insert signals based on a strategy: end #############


######## tasks: start ########

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_usd_jpy_1m_task(block_name: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_usd_jpy_1m(conn)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_usd_jpy_5m_task(block_name: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_usd_jpy_5m(conn)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_usd_jpy_30m_task(block_name: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_usd_jpy_30m(conn)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_usd_jpy_1h_task(block_name: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_usd_jpy_1h(conn)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_usd_jpy_4h_task(block_name: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_usd_jpy_4h(conn)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_rsi_task(block_name: str,
                    rsi_params: dict | None = None,
                    ):
    params = _build_rsi_params(rsi_params)
    with SqlAlchemyConnector.load(block_name) as conn:
        update_rsi(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_sma_task(block_name: str,
                    sma_params: dict | None = None,
                    ):
    params = _build_sma_params(sma_params)
    with SqlAlchemyConnector.load(block_name) as conn:
        update_sma(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def insert_golden_cross_task(block_name: str,
                             sma_golden_cross_params: dict | None = None
                             ):
    params = _build_sma_golden_cross_params()
    with SqlAlchemyConnector.load(block_name) as conn:
        insert_sma_golden_cross(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def insert_dead_cross_task(block_name: str,
                           sma_dead_cross_param: dict | None = None):
    params = _build_sma_dead_cross_params(sma_dead_cross_param)
    with SqlAlchemyConnector.load(block_name) as conn:
        insert_sma_dead_cross(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_ema_task(block_name: str,
                    ema_params: dict | None = None):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_ema(conn, **ema_params)

######## tasks: end ########

######## flows: start ########

@flow
def ohlc(block_name: str = "forex-connector"):
    # 最初に実行
    t1 = update_usd_jpy_1m_task(block_name)

    # 他は並列で実行
    t2 = update_usd_jpy_5m_task.submit(block_name)
    t3 = update_usd_jpy_30m_task.submit(block_name)
    t4 = update_usd_jpy_1h_task.submit(block_name)
    t5 = update_usd_jpy_4h_task.submit(block_name)

    futures = [t2, t3, t4, t5]

    return futures

@flow
def indicator(block_name: str = "forex-connector"):

    # call of rsi
    rsi_periods = RSI_FLOW_DEFAULT_PARAMS.get("periods")
    rsi_timeframes = RSI_FLOW_DEFAULT_PARAMS.get("timeframes")
    rsi_params = _build_rsi_params()
    rsi_futures = []
    for timeframe_code in rsi_timeframes:
        for period in rsi_periods:
            f = update_rsi_task.submit(
                block_name,
                rsi_params={**rsi_params, "period": period, "timeframe_code": timeframe_code},
            )
            rsi_futures.append(f)

    # call of sma
    sma_periods = SMA_FLOW_DEFAULT_PARAMS.get("periods")
    sma_timeframes = SMA_FLOW_DEFAULT_PARAMS.get("timeframes")
    sma_params = _build_sma_params()
    sma_futures = []
    for timeframe_code in sma_timeframes:
        for period in sma_periods:
            f = update_sma_task.submit(
                block_name,
                sma_params={**sma_params, "period": period, "timeframe_code": timeframe_code},
            )
            sma_futures.append(f)

    # call of ema
    ema_periods = EMA_FLOW_DEFAULT_PARAMS.get("periods")
    ema_timeframes = EMA_FLOW_DEFAULT_PARAMS.get("timeframes")
    ema_params = _build_ema_params()
    ema_futures = []
    for timeframe_code in ema_timeframes:
        for period in ema_periods:
            f = update_ema_task.submit(
                block_name,
                ema_params={**ema_params, "period": period, "timeframe_code": timeframe_code},
            )
            ema_futures.append(f)

    return rsi_futures + sma_futures + ema_futures

@flow
def strategy(block_name: str = "forex-connector"):
    """
    add strategy tasks here
    """
    insert_golden_cross_task(block_name)
    insert_dead_cross_task(block_name)

######## flows: start ########



if __name__ == "__main__":
    ohlc()
    indicator()
