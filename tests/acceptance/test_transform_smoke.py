import etl.flows.transform as transform

class _DummyTask:
    def __init__(self):
        self.calls = []

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
    pass

def test_transform_strategy_smoke():
    pass

