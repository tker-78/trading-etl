from config.config import *

##### helpers: start ########
def ticker_table(currency_pair_code: str) -> str:
    return f"ticker_{currency_pair_code.replace('/', '_').lower()}"

def ohlc_table(currency_pair_code: str, timeframe_code: str):
    return f"{currency_pair_code.replace('/', '_').lower()}_{timeframe_code}"



def get_ids(connector, currency_pair_code: str, timeframe_code: str) -> tuple[int, int]:
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

def build_rsi_params(overrides: dict | None = None) -> dict:
    return {**RSI_TASK_DEFAULT_PARAMS, **(overrides or {})}

def build_sma_params(overrides: dict | None = None) -> dict:
    return {**SMA_TASK_DEFAULT_PARAMS, **(overrides or {})}

def build_sma_golden_cross_params(overrides: dict | None = None) -> dict:
    return {**SMA_GOLDEN_CROSS_PARAMS, **(overrides or {})}

def build_sma_dead_cross_params(overrides: dict | None = None) -> dict:
    return {**SMA_DEAD_CROSS_PARAMS, **(overrides or {})}

def build_ema_params(overrides: dict | None = None) -> dict:
    return {**EMA_TASK_DEFAULT_PARAMS, **(overrides or {})}

##### helpers: end ########
