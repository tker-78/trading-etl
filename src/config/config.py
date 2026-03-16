import os
from dotenv import load_dotenv

load_dotenv()


### General setting params ###

SCHEMA_NAME_OHLC = "ohlc"
SCHEMA_NAME_TICKER = "ticker"


### params for indicator setting ###

RSI_TASK_DEFAULT_PARAMS = {
    "period": int(os.getenv("DEFAULT_PERIOD", 14)),
    "currency_pair_code": str(os.getenv("DEFAULT_CURRENCY_PAIR_CODE", "USD/JPY")),
    "timeframe_code": str(os.getenv("DEFAULT_TIMEFRAME_CODE", "1m")),
}

RSI_FLOW_DEFAULT_PARAMS = {
    "periods": [int(period) for period in os.getenv("DEFAULT_PERIODS", "14,28,56").split(",")],
    "timeframes": [str(timeframe) for timeframe in os.getenv("DEFAULT_TIMEFRAMES", "1m,5m,30m,1h,4h").split(",")],
}

SMA_TASK_DEFAULT_PARAMS = {
    "period":  int(os.getenv("DEFAULT_PERIOD", 14)),
    "currency_pair_code": str(os.getenv("DEFAULT_CURRENCY_PAIR_CODE", "USD/JPY")),
    "timeframe_code": str(os.getenv("DEFAULT_TIMEFRAME_CODE", "1m"))
}

SMA_FLOW_DEFAULT_PARAMS = {
    "periods": [int(period) for period in os.getenv("DEFAULT_PERIODS", "14,28,56").split(",")],
    "timeframes": [str(timeframe) for timeframe in os.getenv("DEFAULT_TIMEFRAMES", "1m,5m,30m,1h,4h").split(",")],
}

SMA_GOLDEN_CROSS_PARAMS = {
    "short_period": int(os.getenv("DEFAULT_SHORT_PERIOD", 14)),
    "long_period": int(os.getenv("DEFAULT_LONG_PERIOD", 28)),
}

SMA_DEAD_CROSS_PARAMS = {
    "short_period": int(os.getenv("DEFAULT_SHORT_PERIOD", 14)),
    "long_period": int(os.getenv("DEFAULT_LONG_PERIOD", 28)),
}


EMA_TASK_DEFAULT_PARAMS = {
    "period":  int(os.getenv("DEFAULT_PERIOD", 14)),
    "currency_pair_code": str(os.getenv("DEFAULT_CURRENCY_PAIR_CODE", "USD/JPY")),
    "timeframe_code": str(os.getenv("DEFAULT_TIMEFRAME_CODE", "1m"))
}

EMA_FLOW_DEFAULT_PARAMS = {
    "periods": [int(period) for period in os.getenv("DEFAULT_PERIODS", "14,28,56").split(",")],
    "timeframes": [str(timeframe) for timeframe in os.getenv("DEFAULT_TIMEFRAMES", "1m,5m,30m,1h,4h").split(",")],
}

