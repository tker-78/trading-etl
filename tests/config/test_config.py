import os
import importlib

import pytest

import src.config.db_config as db_config
import src.config.config as config


def test_db_config_import():
    env = os.getenv('APP_ENV')
    assert env == 'test'
    db_url = db_config.get_db_url()
    assert db_url.database == 'forex-test'


def reload_config():
    return importlib.reload(config)


def test_indicator_defaults_when_env_not_set(monkeypatch):
    for env_name in [
        "DEFAULT_PERIOD",
        "DEFAULT_CURRENCY_PAIR_CODE",
        "DEFAULT_TIMEFRAME_CODE",
        "DEFAULT_PERIODS",
        "DEFAULT_TIMEFRAMES",
    ]:
        monkeypatch.delenv(env_name, raising=False)

    loaded = reload_config()

    assert loaded.RSI_TASK_DEFAULT_PARAMS == {
        "period": 14,
        "currency_pair_code": "USD/JPY",
        "timeframe_code": "1m",
    }
    assert loaded.RSI_FLOW_DEFAULT_PARAMS == {
        "periods": [14, 28, 56],
        "timeframes": ["1m", "5m", "30m", "1h", "4h"],
    }


def test_indicator_env_overrides(monkeypatch):
    monkeypatch.setenv("DEFAULT_PERIOD", "21")
    monkeypatch.setenv("DEFAULT_CURRENCY_PAIR_CODE", "EUR/JPY")
    monkeypatch.setenv("DEFAULT_TIMEFRAME_CODE", "5m")
    monkeypatch.setenv("DEFAULT_PERIODS", "7,21,42")
    monkeypatch.setenv("DEFAULT_TIMEFRAMES", "5m,15m,1h")

    loaded = reload_config()

    assert loaded.SMA_TASK_DEFAULT_PARAMS == {
        "period": 21,
        "currency_pair_code": "EUR/JPY",
        "timeframe_code": "5m",
    }
    assert loaded.EMA_FLOW_DEFAULT_PARAMS == {
        "periods": [7, 21, 42],
        "timeframes": ["5m", "15m", "1h"],
    }


def test_invalid_integer_env_raises(monkeypatch):
    monkeypatch.setenv("DEFAULT_PERIOD", "abc")

    with pytest.raises(ValueError, match="DEFAULT_PERIOD must be an integer"):
        reload_config()


def test_invalid_integer_list_env_raises(monkeypatch):
    monkeypatch.setenv("DEFAULT_PERIODS", "14,,56")

    with pytest.raises(ValueError, match="DEFAULT_PERIODS must be a comma-separated list of integers"):
        reload_config()
