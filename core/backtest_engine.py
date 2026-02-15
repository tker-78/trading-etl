# backtest engine

class BacktestEngine: pass

class BacktestFX(BacktestEngine):
    def __init__(self):
        ...

    def _load_yaml(self):
        """
        トレードシナリオ定義のyamlファイルを
        """
        ...

    def generate_buysell_events(self):
        """
        yamlファイルの内容をもとにしてfact_buysell_eventsテーブルにevent情報を生成する
        """
        ...

    def run(self):
        """
        fact_buysell_eventsの情報を参照してトレードを実行する。
        """
        ...



