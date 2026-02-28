from sqlalchemy.sql.elements import quoted_name
import numpy as np
import talib
from prefect_sqlalchemy import SqlAlchemyConnector
from config.config import *
import transform_helpers as helpers

######### create ticker tables: start #########
def create_ticker_tables(connector):
    select_query = """
                   SELECT currency_pair_code
                   FROM dim_currency; \
                   """
    rows = connector.execute(select_query).all()

    for pair in rows:
        schema_name = quoted_name(SCHEMA_NAME_TICKER, quote=True)
        tablename = quoted_name(helpers.ticker_table(pair[0]), quote=True)
        create_query = f"""
        CREATE TABLE IF NOT EXISTS {schema_name}.{tablename} (
            time TIMESTAMP PRIMARY KEY,
            bid FLOAT,
            ask FLOAT
        );
        """
        connector.execute(create_query)

######### create ticker tables: end #########

######### create OHLC tables: start ##############



######### create OHLC tables: end ##############
def create_ohlc_tables(connector: SqlAlchemyConnector, *, currency_pair_code: str, timeframe_code: str):
    """
    各通貨ペアのテーブルを作成する
    """
    schema_name = quoted_name(SCHEMA_NAME_OHLC, quote=True)
    ohlc_table = quoted_name(helpers.ohlc_table(currency_pair_code, timeframe_code), quote=True)
    query = f"""
    CREATE TABLE IF NOT EXISTS {schema_name}.{ohlc_table} (
        time TIMESTAMP PRIMARY KEY,
        open FLOAT,
        high FLOAT,
        low FLOAT,
        close FLOAT
    );
    """
    connector.execute(query)



######### update OHLC tables ##############

def update_ohlc_base_tables(connector: SqlAlchemyConnector, *, currency_pair_code: str, timeframe_code: str):
    """
    各通貨ペアのベースになるohlc(デフォルトは1 minute)のデータを生成する。
    """
    ohlc_schema_name = quoted_name(SCHEMA_NAME_OHLC, quote=True)
    ticker_schema_name = quoted_name(SCHEMA_NAME_TICKER, quote=True)
    ohlc_table = quoted_name(helpers.ohlc_table(currency_pair_code, timeframe_code), quote=True)

    query = f"""
    INSERT INTO {ohlc_schema_name}.{ohlc_table} (time, open, high, low, close)
    WITH bucket_time AS (
    SELECT 
    date_trunc('minute', time) AS bucket,
    time, 
    bid
    FROM {ticker_schema_name}.{helpers.ticker_table(currency_pair_code)}
    )
    SELECT
    bucket AS time,
    -- open
    (array_agg(bid ORDER BY time))[1] AS open,
    -- high
    MAX(bid) AS high,
    -- low
    MIN(bid) AS low,
    -- close
    (array_agg(bid ORDER BY time DESC))[1] AS close
    FROM bucket_time
    GROUP BY bucket
    ON CONFLICT DO NOTHING;
    """
    connector.execute(query)



# def update_usd_jpy_1m(connector):
#     query = """
# INSERT INTO ohlc.usd_jpy_1m (time, open, high, low, close)
# WITH bucket_time AS (
# SELECT
#     DATE_TRUNC('minute', time) AS bucket,
#     time,
#     bid
# FROM ticker.ticker_usd_jpy
# )
# SELECT
# bucket AS time,
# (array_agg(bid ORDER BY time))[1] AS open,
# MAX(bid) AS high,
# MIN(bid) AS low,
# (array_agg(bid ORDER BY time DESC))[1] AS close
# FROM bucket_time
# GROUP BY bucket
# ON CONFLICT DO NOTHING;
#     """
#     connector.execute(query)

def update_usd_jpy_5m(connector):
    query = """
            INSERT INTO ohlc.usd_jpy_5m (time, open, high, low, close)
            WITH bucket_time AS (
                SELECT
                    date_trunc('minute', time) - (EXTRACT(minute FROM time)::int % 5) * interval  '1 minute' AS bucket,
                    time,
                    open,
                    high,
                    low,
                    close
                FROM ohlc.usd_jpy_1m
            )
            SELECT
                bucket AS time,
                (array_agg(open ORDER BY bucket))[1] AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                (array_agg(close ORDER BY time DESC))[1] AS close
            FROM bucket_time
            GROUP BY bucket
            ON CONFLICT DO NOTHING; \
            """
    connector.execute(query)

def update_usd_jpy_30m(connector):
    query = """
            INSERT INTO ohlc.usd_jpy_30m (time, open, high, low, close)
            WITH bucket_time AS (
                SELECT
                    date_trunc('minute', time) - (EXTRACT(minute FROM time)::int % 30) * interval  '1 minute' AS bucket,
                    time,
                    open,
                    high,
                    low,
                    close
                FROM ohlc.usd_jpy_1m
            )
            SELECT
                bucket AS time,
                (array_agg(open ORDER BY bucket))[1] AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                (array_agg(close ORDER BY time DESC))[1] AS close
            FROM bucket_time
            GROUP BY bucket
            ON CONFLICT DO NOTHING; \
            """
    connector.execute(query)

def update_usd_jpy_1h(connector):
    query = """
            INSERT INTO ohlc.usd_jpy_1h (time, open, high, low, close)
            WITH bucket_time AS (
                SELECT
                    date_trunc('hour', time) AS bucket,
                    time,
                    open,
                    high,
                    low,
                    close
                FROM ohlc.usd_jpy_1m
            )
            SELECT
                bucket AS time,
                (array_agg(open ORDER BY time))[1] AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                (array_agg(close ORDER BY time DESC))[1] AS close
            FROM bucket_time
            GROUP BY bucket
            ON CONFLICT DO NOTHING; \
            """
    connector.execute(query)

def update_usd_jpy_4h(connector):
    query = """
            INSERT INTO ohlc.usd_jpy_4h (time, open, high, low, close)
            WITH bucket_time AS (
                SELECT
                    date_trunc('hour', time) - (EXTRACT(hour FROM time)::int % 4) * interval '1 hour' AS bucket,
                    time,
                    open,
                    high,
                    low,
                    close
                FROM ohlc.usd_jpy_1m
            )
            SELECT
                bucket AS time,
                (array_agg(open ORDER BY time))[1] AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                (array_agg(close ORDER BY time DESC))[1] AS close
            FROM bucket_time
            GROUP BY bucket
            ON CONFLICT DO NOTHING; \
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

    schema_name = quoted_name(SCHEMA_NAME_OHLC, quote=True)
    table_name = quoted_name(helpers.ohlc_table(currency_pair_code, timeframe_code), quote=True)
    table_name = f"{schema_name}.{table_name}"

    currency_id, timeframe_id = helpers.get_ids(connector, currency_pair_code, timeframe_code)

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
                   ON CONFLICT DO NOTHING; \
                   """
    connector.execute(insert_query, insert_rows)

def update_sma(connector,
               *,
               period: int,
               currency_pair_code: str,
               timeframe_code: str
               ):

    _calc_version = 0

    schema_name = quoted_name(SCHEMA_NAME_OHLC, quote=True)
    table_name = quoted_name(helpers.ohlc_table(currency_pair_code, timeframe_code), quote=True)
    table_name = f"{schema_name}.{table_name}"

    currency_id, timeframe_id = helpers.get_ids(connector, currency_pair_code, timeframe_code)

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
                   ON CONFLICT DO NOTHING; \
                   """
    connector.execute(insert_query, insert_rows)

def update_ema(connector,
               *,
               period: int,
               currency_pair_code: str,
               timeframe_code: str
               ):

    _calc_version = 0

    schema_name = quoted_name(SCHEMA_NAME_OHLC, quote=True)
    table_name = quoted_name(helpers.ohlc_table(currency_pair_code, timeframe_code), quote=True)
    table_name = f"{schema_name}.{table_name}"

    currency_id, timeframe_id = helpers.get_ids(connector, currency_pair_code, timeframe_code)

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
            ON CONFLICT DO NOTHING; \

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

