from prefect import flow

from prefect_sqlalchemy import SqlAlchemyConnector
from config.config import *
from transform_tasks import (
create_ticker_tables_task,
create_ohlc_tables_task,
update_ohlc_base_tables_task,
update_ohlc_derived_tables_task,
update_rsi_task,
update_ema_task,
update_sma_task,
insert_dead_cross_task,
insert_golden_cross_task,
)
import transform_helpers as helpers


@flow
def ticker(block_name: str = "forex-connector"):
    create_ticker_tables_task(block_name)

@flow
def ohlc_pipeline(block_name: str = "forex-connector"):
    create_state = create_ohlc_tables.with_options(name="create-ohlc")(block_name)
    update_ohlc_tables.with_options(name="update-ohlc")(block_name, wait_for=[create_state])

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
def update_ohlc_tables(block_name = "forex-connector"):
    currencies = None
    timeframes = None
    base_timeframe_code = "1m"

    query = f"""
    SELECT DISTINCT currency_pair_code
    FROM dim_currency;
    """
    currencies = list(SqlAlchemyConnector.load(block_name).execute(query).scalars())

    query = f"""
    SELECT DISTINCT timeframe_code, duration_seconds
    FROM dim_timeframe;
    """
    result = SqlAlchemyConnector.load(block_name).execute(query)
    timeframes = result.all()
    timeframes_dict = {timeframe_code: duration_seconds for timeframe_code, duration_seconds in timeframes}
    print(timeframes_dict)

    for currency_pair_code in currencies:
        base_future = update_ohlc_base_tables_task.submit(block_name, currency_pair_code, base_timeframe_code)
        for timeframe in timeframes_dict:
            if timeframe != base_timeframe_code:
                update_ohlc_derived_tables_task.submit(
                    block_name,
                    currency_pair_code,
                    timeframe,
                    timeframes_dict[timeframe],
                    base_timeframe_code,
                    wait_for=[base_future]
                )


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



if __name__ == "__main__":
    ohlc_pipeline()
    # indicator()
