from prefect import task
from prefect_sqlalchemy import SqlAlchemyConnector
from src.etl.flows.transform_services import (
create_ticker_tables,
create_ohlc_tables,
update_ohlc_base_tables,
update_ohlc_derived_tables,
update_ema,
update_rsi,
update_sma,
insert_sma_golden_cross,
insert_sma_dead_cross,
)
import src.etl.flows.transform_helpers as helpers

######## tasks: start ########

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def create_ticker_tables_task(block_name: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        create_ticker_tables(conn)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_ohlc_base_tables_task(block_name: str, currency_pair_code: str, base_timeframe_code: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_ohlc_base_tables(conn, currency_pair_code, base_timeframe_code)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_ohlc_derived_tables_task(
        block_name: str,
        currency_pair_code: str,
        timeframe_code: str,
        timeframe_duration_seconds: int,
        base_timeframe_code: str = '1m'):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_ohlc_derived_tables(
            conn,
            currency_pair_code,
            timeframe_code,
            timeframe_duration_seconds,
            base_timeframe_code)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def create_ohlc_tables_task(block_name: str, currency_pair_code: str, timeframe_code: str):
    with SqlAlchemyConnector.load(block_name) as conn:
        create_ohlc_tables(conn, currency_pair_code=currency_pair_code, timeframe_code=timeframe_code)


@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_rsi_task(block_name: str,
                    rsi_params: dict | None = None,
                    ):
    params = helpers.build_rsi_params(rsi_params)
    with SqlAlchemyConnector.load(block_name) as conn:
        update_rsi(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_sma_task(block_name: str,
                    sma_params: dict | None = None,
                    ):
    params = helpers.build_sma_params(sma_params)
    with SqlAlchemyConnector.load(block_name) as conn:
        update_sma(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def insert_golden_cross_task(block_name: str,
                             sma_golden_cross_params: dict | None = None
                             ):
    params = helpers.build_sma_golden_cross_params()
    with SqlAlchemyConnector.load(block_name) as conn:
        insert_sma_golden_cross(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def insert_dead_cross_task(block_name: str,
                           sma_dead_cross_param: dict | None = None):
    params = helpers.build_sma_dead_cross_params(sma_dead_cross_param)
    with SqlAlchemyConnector.load(block_name) as conn:
        insert_sma_dead_cross(conn, **params)

@task(retries=2, retry_delay_seconds=30, log_prints=True)
def update_ema_task(block_name: str,
                    ema_params: dict | None = None):
    with SqlAlchemyConnector.load(block_name) as conn:
        update_ema(conn, **ema_params)

######## tasks: end ########
