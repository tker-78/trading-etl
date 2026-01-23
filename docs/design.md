# Design

アプリケーション全体として、下記のレイヤーを持つ。

- Ingest: データの取得
- ETL Orchestration: データの整形・再計算
- Analytic: データの分析・可視化
- Execution: トレードの実行
- Control: 状態監視と制御


## Ingest

Websocketを使う。
GMO Coinのwebsocketサーバーと接続する。

raw_storeに保存する。


## ETL Orchestration

Prefectを使う。
raw_storeからバッチ処理で各時間足のOHLCデータを生成する。
分析の要求に応じてETL処理内容は書き換え・追加する必要がある。

## Analytic

Supersetを使う。
この分析を使ってトレードルールを研究する。
分析結果をExecutionに自動反映することはしない。


## Execution

リアルタイムデータをもとにTalibなどで分析した結果をもとにトレードを実行する。
この層はスクラッチ開発。
この層の処理内容は完全に自律しており、他のプロセスから干渉を受けない。
(実行のON/OFFのみはFastAPIから実行する)

## Control

FastAPIを使う。
フロントエンドはVue.jsを選択する。

この層は、薄い制御及び可視化の用途で使う。

- リアルタイムデータチャート表示: /charts/realtime
- 死活監視: /health
- データ遅延: /status/delay
- ETL状態: /status/etl
- 最新時刻: /status/last_tick
- 取引状況
  - ポジション: /trade-status/position
  - 残高: /trade-status/balance



## 設計原則
禁止ルール
- Control は Execution ロジックを持たない
- ETL は Execution に直接影響しない
- Analytic は自動で Execution を変更しない
- Execution は ETL をトリガしない
