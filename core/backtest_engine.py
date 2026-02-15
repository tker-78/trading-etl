# backtest engine
from typing import Optional
from database.base import session_scope

class BacktestEngine: pass

class BacktestFX(BacktestEngine):
    def __init__(self):
        ...

    def _load_yaml(self) -> Optional[dict]:
        """
        トレードシナリオ定義のyamlファイルを
        """
        return None

    def _generate_buysell_events(self):
        """
        yamlファイルの内容をもとにしてfact_buysell_eventsテーブルにevent情報を生成する
        """
        config_dict = self._load_yaml()

        # prefectのstrategy flowを走らせる。

        # flowの完了を待つ

        with session_scope() as session:
            # fact_buysell_eventsにeventが生成されたことを確認する。
            # eventが0件であれば通知する
            ...




    def run(self):
        """
        fact_buysell_eventsの情報を参照してトレードを実行する。
        """
        # config_dictで指定した条件に基づき、時系列でeventを処理して、
        # 資金の増減を記録する。



