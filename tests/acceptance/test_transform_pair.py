import etl.flows.transform as transform


class _DummyTask:
    def submit(self, *args, **kwargs):
        return object()


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
        raise AssertionError(f"Unexpected query: {normalized}")


class _FakeSqlAlchemyConnector:
    connector = _FakeConnector()

    @classmethod
    def load(cls, _block_name):
        return cls.connector


def test_transform_pair_uses_mocked_connector(monkeypatch):
    monkeypatch.setattr(transform, "SqlAlchemyConnector", _FakeSqlAlchemyConnector)
    monkeypatch.setattr(transform, "update_ohlc_base_tables_task", _DummyTask())
    monkeypatch.setattr(transform, "update_ohlc_derived_tables_task", _DummyTask())
    _FakeSqlAlchemyConnector.connector.queries.clear()

    transform.update_ohlc_tables.fn(block_name="test-connector")

    assert len(_FakeSqlAlchemyConnector.connector.queries) == 2
