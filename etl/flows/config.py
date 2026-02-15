RSI_TASK_DEFAULT_PARAMS = {
    "period": 14,
    "currency_pair_code": "USD/JPY",
    "timeframe_code": "1m",
}

RSI_FLOW_DEFAULT_PARAMS = {
    "periods": [14, 28, 56],
    "timeframes": ["1m", "5m", "30m", "1h", "4h"],
}

SMA_TASK_DEFAULT_PARAMS = {
    "period":  14,
    "currency_pair_code": "USD/JPY",
    "timeframe_code": "1m",
}

SMA_FLOW_DEFAULT_PARAMS = {
    "periods": [14, 28, 56],
    "timeframes": ["1m", "5m", "1h"],
}

SMA_GOLDEN_CROSS_PARAMS = {
    "short_period": 14,
    "long_period": 28,
    # "timeframe_code": "1m",
    # "currency_pair_code": "USD/JPY",
}

SMA_DEAD_CROSS_PARAMS = {
    "short_period": 14,
    "long_period": 28,
}
