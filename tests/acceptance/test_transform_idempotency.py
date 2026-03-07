import etl.flows.transform as transform
import etl.flows.transform_services as transform_services


class _RecordingTask:
    def __init__(self):
        self.calls = []

    def submit(self, *args, **kwargs): ...


class _FakeExecuteResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self): ...

    def all(self): ...


class _FakeSqlAlchemyConnector: ...


def test_update_ohlc_tables_multi_pair_wait_for(monkeypatch):
    base_task = _RecordingTask()
    derived_task = _RecordingTask

    monkeypatch.setattr(transform, "SqlAlchemyConnector", _FakeSqlAlchemyConnector)
