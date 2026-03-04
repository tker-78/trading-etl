import etl.flows.transform as transform

class _DummyTask:
    ...

class _FakeExecuteResult:
    ...

class _FakeConnector:
    ...

class _FakeSqlAlchemyConnector:
    connector = _FakeConnector()

def test_transform_pair_uses_mocked_connector(monkeypatch):
    monkeypatch.setattr(transform, "SqlAlchemyConnector", _FakeSqlAlchemyConnector)
    monkeypatch.setattr(transform, "update_ohlc_base_tables_task", _DummyTask())
    monkeypatch.setattr(transform, "update_ohlc_derived_tables_task", _DummyTask())
    _FakeSqlAlchemyConnector.connector.queries.clear()

