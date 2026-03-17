import os
from dotenv import load_dotenv

load_dotenv()


### General setting params ###

SCHEMA_NAME_OHLC = "ohlc"
SCHEMA_NAME_TICKER = "ticker"


### params for indicator setting ###

DEFAULT_PERIOD = 14
DEFAULT_CURRENCY_PAIR_CODE = "USD/JPY"
DEFAULT_TIMEFRAME_CODE = "1m"
DEFAULT_PERIODS = [14, 28, 56]
DEFAULT_TIMEFRAMES = ["1m", "5m", "30m", "1h", "4h"]
DEFAULT_SHORT_PERIOD = 14
DEFAULT_LONG_PERIOD = 28


def _get_str_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default

    stripped = value.strip()
    if not stripped:
        raise ValueError(f"{name} must not be empty")
    return stripped


def _get_int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default

    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer: {value!r}") from exc


def _get_int_list_env(name: str, default: list[int]) -> list[int]:
    value = os.getenv(name)
    if value is None:
        return default

    items = [item.strip() for item in value.split(",")]
    if not items or any(not item for item in items):
        raise ValueError(f"{name} must be a comma-separated list of integers")

    try:
        return [int(item) for item in items]
    except ValueError as exc:
        raise ValueError(f"{name} must be a comma-separated list of integers: {value!r}") from exc


def _get_str_list_env(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default

    items = [item.strip() for item in value.split(",")]
    if not items or any(not item for item in items):
        raise ValueError(f"{name} must be a comma-separated list of strings")
    return items

RSI_TASK_DEFAULT_PARAMS = {
    "period": _get_int_env("DEFAULT_PERIOD", DEFAULT_PERIOD),
    "currency_pair_code": _get_str_env("DEFAULT_CURRENCY_PAIR_CODE", DEFAULT_CURRENCY_PAIR_CODE),
    "timeframe_code": _get_str_env("DEFAULT_TIMEFRAME_CODE", DEFAULT_TIMEFRAME_CODE),
}

RSI_FLOW_DEFAULT_PARAMS = {
    "periods": _get_int_list_env("DEFAULT_PERIODS", DEFAULT_PERIODS),
    "timeframes": _get_str_list_env("DEFAULT_TIMEFRAMES", DEFAULT_TIMEFRAMES),
}

SMA_TASK_DEFAULT_PARAMS = {
    "period": _get_int_env("DEFAULT_PERIOD", DEFAULT_PERIOD),
    "currency_pair_code": _get_str_env("DEFAULT_CURRENCY_PAIR_CODE", DEFAULT_CURRENCY_PAIR_CODE),
    "timeframe_code": _get_str_env("DEFAULT_TIMEFRAME_CODE", DEFAULT_TIMEFRAME_CODE),
}

SMA_FLOW_DEFAULT_PARAMS = {
    "periods": _get_int_list_env("DEFAULT_PERIODS", DEFAULT_PERIODS),
    "timeframes": _get_str_list_env("DEFAULT_TIMEFRAMES", DEFAULT_TIMEFRAMES),
}

SMA_GOLDEN_CROSS_PARAMS = {
    "short_period": _get_int_env("DEFAULT_SHORT_PERIOD", DEFAULT_SHORT_PERIOD),
    "long_period": _get_int_env("DEFAULT_LONG_PERIOD", DEFAULT_LONG_PERIOD),
}

SMA_DEAD_CROSS_PARAMS = {
    "short_period": _get_int_env("DEFAULT_SHORT_PERIOD", DEFAULT_SHORT_PERIOD),
    "long_period": _get_int_env("DEFAULT_LONG_PERIOD", DEFAULT_LONG_PERIOD),
}


EMA_TASK_DEFAULT_PARAMS = {
    "period": _get_int_env("DEFAULT_PERIOD", DEFAULT_PERIOD),
    "currency_pair_code": _get_str_env("DEFAULT_CURRENCY_PAIR_CODE", DEFAULT_CURRENCY_PAIR_CODE),
    "timeframe_code": _get_str_env("DEFAULT_TIMEFRAME_CODE", DEFAULT_TIMEFRAME_CODE),
}

EMA_FLOW_DEFAULT_PARAMS = {
    "periods": _get_int_list_env("DEFAULT_PERIODS", DEFAULT_PERIODS),
    "timeframes": _get_str_list_env("DEFAULT_TIMEFRAMES", DEFAULT_TIMEFRAMES),
}
