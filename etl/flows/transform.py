from prefect import flow

from prefect_sqlalchemy import SqlAlchemyConnector
from config.config import *
from transform_tasks import (
create_ticker_tables_task,
create_ohlc_tables_task,
update_ohlc_base_tables_task,
update_rsi_task,
update_ema_task,
update_sma_task,
insert_dead_cross_task,
insert_golden_cross_task,
)
import transform_helpers as helpers


######## flows: start ########

@flow
def ticker(block_name: str = "forex-connector"):
    create_ticker_tables_task(block_name)

@flow
def create_ohlc_tables(block_name = "forex-connector"):
    query = f"""
    SELECT DISTINCT currency_pair_code
    FROM dim_currency;
    """
    currencies = list(SqlAlchemyConnector.load(block_name).execute(query).scalars())

    query = f"""
    SELECT DISTINCT timeframe_code
    FROM dim_timeframe;
    """
    timeframes = list(SqlAlchemyConnector.load(block_name).execute(query).scalars())

    for currency in currencies:
        for timeframe in timeframes:
            create_ohlc_tables_task.submit(block_name, currency, timeframe)

@flow
def update_ohlc_base_tables(block_name = "forex-connector"):
    currencies = None
    timeframes = None

    query = f"""
    SELECT DISTINCT currency_pair_code
    FROM dim_currency;
    """
    currencies = list(SqlAlchemyConnector.load(block_name).execute(query).scalars())

    for currency in currencies:
        update_ohlc_base_tables_task.submit(block_name, currency, "1m")


# @flow
# def ohlc(block_name: str = "forex-connector"):
#     # 最初に実行
#     t1 = update_usd_jpy_1m_task(block_name)
#
#     # 他は並列で実行
#     t2 = update_usd_jpy_5m_task.submit(block_name)
#     t3 = update_usd_jpy_30m_task.submit(block_name)
#     t4 = update_usd_jpy_1h_task.submit(block_name)
#     t5 = update_usd_jpy_4h_task.submit(block_name)
#
#     futures = [t2, t3, t4, t5]
#
#     return futures

@flow
def indicator(block_name: str = "forex-connector"):

    # call of rsi
    rsi_periods = RSI_FLOW_DEFAULT_PARAMS.get("periods")
    rsi_timeframes = RSI_FLOW_DEFAULT_PARAMS.get("timeframes")
    rsi_params = helpers.build_rsi_params()
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
    sma_params = helpers.build_sma_params()
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
    ema_params = helpers.build_ema_params()
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
    create_ohlc_tables()
    update_ohlc_base_tables()
    # indicator()
    # ticker()
