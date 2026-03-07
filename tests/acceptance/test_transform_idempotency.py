import etl.flows.transform as transform
import etl.flows.transform_services as transform_services


class _RecordingTask:
    def __init__(self):
        self.calls = []

    def submit(self, *args, **kwargs):
        future = object()
        self.calls.append({"args": args, "kwargs": kwargs, "future": future})
        return future


class _FakeExecuteResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        return iter(self._rows)

    def all(self):
        return list(self._rows)

class _FakeConnector:
    def __init__(self):
        self.queries = []

    def execute(self, query):
        self.queries.append(query)
        normalized = " ".join(query.split())

        if "SELECT DISTINCT currency_pair_code FROM dim_currency;" in normalized:
            return _FakeExecuteResult(["USD/JPY", "EUR/JPY"])
        if "SELECT DISTINCT timeframe_code, duration_seconds FROM dim_timeframe;" in normalized:
            return _FakeExecuteResult([("1m", 60), ("5m", 300)])
        if "SELECT DISTINCT timeframe_code FROM dim_timeframe;" in normalized:
            return _FakeExecuteResult(["1m", "5m"])
        raise AssertionError(f"Unexpected query: {normalized}")

class _FakeSqlAlchemyConnector:
    connector = _FakeConnector()

    @classmethod
    def load(cls, _block_name):
        return cls.connector

class _CaptureConnector:
    """
    発行したクエリを保存し、空のリザルトを返す
    """
    def __init__(self):
        self.calls = []
    def execute(self, query, params=None):
        self.calls.append({"query": query, "params": params})
        return _FakeExecuteResult([])



def test_update_ohlc_tables_multi_pair_wait_for(monkeypatch):
    base_task = _RecordingTask()
    derived_task = _RecordingTask()

    monkeypatch.setattr(transform, "SqlAlchemyConnector", _FakeSqlAlchemyConnector)
    monkeypatch.setattr(transform, "update_ohlc_base_tables_task", base_task)
    monkeypatch.setattr(transform, "update_ohlc_derived_tables_task", derived_task)
    _FakeSqlAlchemyConnector.connector.queries.clear()

    transform.update_ohlc_tables.fn(block_name="test-connector")

    assert len(base_task.calls) == 2
    assert [call["args"] for call in base_task.calls] == [
        ("test-connector", "USD/JPY", "1m"),
        ("test-connector", "EUR/JPY", "1m"),
    ]

    assert len(derived_task.calls) == 2
    assert [call["args"] for call in derived_task.calls] == [
        ("test-connector", "USD/JPY", "5m", 300, "1m"),
        ("test-connector", "EUR/JPY", "5m", 300, "1m"),
    ]

    base_future_by_pair = {
        call["args"][1]: call["future"]
        for call in base_task.calls
    }
    for call in derived_task.calls:
        pair = call["args"][1]
        assert call["kwargs"]["wait_for"] == [base_future_by_pair[pair]]

def test_create_ohlc_tables_submits_all_currency_timeframe_pairs(monkeypatch):
    create_task = _RecordingTask()

    monkeypatch.setattr(transform, "SqlAlchemyConnector", _FakeSqlAlchemyConnector)
    monkeypatch.setattr(transform, "create_ohlc_tables_task", create_task)
    _FakeSqlAlchemyConnector.connector.queries.clear()

    transform.create_ohlc_tables.fn(block_name="test-connector")

    assert len(create_task.calls) == 4



def test_ohlc_update_queries_use_on_conflict_do_nothing():
    connector = _CaptureConnector()

    transform_services.update_ohlc_base_tables(connector, "USD/JPY", "1m")
    transform_services.update_ohlc_derived_tables(connector, "USD/JPY", "5m", 300, "1m")

    assert len(connector.calls) == 2







