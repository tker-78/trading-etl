import etl.flows.transform as transform

class _DummyTask:
    def __init__(self):
        self.calls = []

    def submit(self, block_name, **kwargs):
        self.calls.append({"block_name": block_name, **kwargs})
        return object()

class _DummyFlow:
    def __init__(self, return_value):
        self.return_value = return_value
        self.options_calls = []
        self.calls = []

    def with_options(self, **kwargs):
        self.options_calls.append(kwargs)

        def _runner(*args, **call_kwargs):
            self.calls.append({"args": args, "kwargs": call_kwargs})
            return self.return_value

        return _runner

def test_transform_ohlc_pipeline_smoke(monkeypatch):
    """
    ohlc pipelineの実行順序をテスト
    """
    create_state = object()
    create_flow = _DummyFlow(return_value=create_state)
    update_flow = _DummyFlow(return_value=None)

    monkeypatch.setattr(transform, "create_ohlc_tables", create_flow)
    monkeypatch.setattr(transform, "update_ohlc_tables", update_flow)

    transform.ohlc_pipeline.fn(block_name="test-connector")

    assert create_flow.options_calls == [{"name": "create-ohlc"}]
    assert update_flow.options_calls == [{"name": "update-ohlc"}]

    # update_flowはcreate_flowを待つこと
    assert len(create_flow.calls) == 1
    assert create_flow.calls[0]["args"] == ("test-connector",)
    assert create_flow.calls[0]["kwargs"] == {}

    assert len(update_flow.calls) == 1
    assert update_flow.calls[0]["args"] == ("test-connector",)
    assert update_flow.calls[0]["kwargs"]["wait_for"] == [create_state]



def test_transform_indicator_smoke(monkeypatch):
    rsi_task = _DummyTask()
    sma_task = _DummyTask()
    ema_task = _DummyTask()

    monkeypatch.setattr(transform, "update_rsi_task", rsi_task)
    monkeypatch.setattr(transform, "update_sma_task", sma_task)
    monkeypatch.setattr(transform, "update_ema_task", ema_task)

    monkeypatch.setattr(transform, "RSI_FLOW_DEFAULT_PARAMS", {"periods": [14], "timeframes": ["1m"]})
    monkeypatch.setattr(transform, "SMA_FLOW_DEFAULT_PARAMS", {"periods": [15], "timeframes": ["5m"]})
    monkeypatch.setattr(transform, "EMA_FLOW_DEFAULT_PARAMS", {"periods": [16], "timeframes": ["10m"]})

    monkeypatch.setattr(transform.helpers, "build_rsi_params", lambda: {"currency_pair_code": "USD/JPY"})

    futures = transform.indicator.fn(block_name="test-connector")

    assert len(futures) == 3

    assert rsi_task.calls[0]["block_name"] == "test-connector"
    assert rsi_task.calls[0]["rsi_params"]["period"] == 14
    assert rsi_task.calls[0]["rsi_params"]["timeframe_code"] == "1m"

    assert sma_task.calls[0]["block_name"] == "test-connector"
    assert sma_task.calls[0]["sma_params"]["period"] == 15
    assert sma_task.calls[0]["sma_params"]["timeframe_code"] == "5m"

    assert ema_task.calls[0]["block_name"] == "test-connector"
    assert ema_task.calls[0]["ema_params"]["period"] == 16
    assert ema_task.calls[0]["ema_params"]["timeframe_code"] == "10m"



def test_transform_strategy_smoke():
    pass
























