# tasks in commonize branch

このドキュメントは、為替データの受信を行う`ws-connection.py`と、
その情報をDBに蓄積し、分析を行う`etl/*`の処理を段階的に実装するための作業計画である。

## T1: USD_JPY以外の通貨ペアにも対応する
- dim_currencyに存在する通貨ペアについて、
  - ticker_{CURRENCY_PAIR_CODE} テーブルを生成する
  - {CURRENCY_PAIR_CODE}_{TIMEFRAME_CODE} テーブルを生成する


## T2: ws-connection.py

- 主要銘柄(下記)のデータを取得する。
  - USD_JPY
  - EUR_JPY
  - GBP_JPY
  - AUD_JPY
  - NZD_JPY
  - CAD_JPY
  - CHF_JPY
- 上記銘柄について、並列でtickerデータをwebsocketで受信する。
- 受信したデータをticker_{CURRENCY_PAIR_CODE}テーブルに保存する。
- Streamerのon_openでsubscribe情報を複数作成して、同一のwebsocket connectionで複数subscribeする。

## T3: DB整理

- ticker, OHLC, dim/factをスキーマに分ける。 
- ws-connection.pyの保存先DBをtickerスキーマに指定する。
- etl/flows/transform.pyのticker取得先スキーマをtickerスキーマに変更する。
- スキーマの指定が煩雑になるので、`psycopg2`の`sql.SQL`を使って識別子を指定する構成に変更する。(**これは不採用**)
```sql
from psycopg2 import sql

schema = "ohlc"
table = "usd_jpy_1m"

q = sql.SQL("SELECT time, close FROM {}.{} ORDER BY time").format(
    sql.Identifier(schema),
    sql.Identifier(table),
)

cur.execute(q)  # 値があるなら cur.execute(q, (value1, ...)) のように別で渡す
```


## T4: ws-connection.py

- 各種通貨ペア毎のクラス、ticker_factoryの生成を共通化する。
- dim_currencyの`currency_pair_symbol`を取得して、動的にクラスを生成する、または
  動的に保存先のテーブルを切り替える。

## T5: ws_ticker_server.py

- 残作業（未完了のみ）:
  - `fetch_rows_after(last_processed_time)` の初回 `None` 扱いを明確化し、テーブル空起動時でも配信ループが継続できるようにする。
  - `ClientRegistry.add()` の戻り値型/戻り値の不整合を整理する（戻り値を返す or `None` に統一）。
  - 接続/切断/拒否ログに `path`, `symbol`, 接続数（拒否時は許可済みpath一覧）を含めて出力する。
  - 受け入れ条件を実機で確認する（`/ws/ticker_usd_jpy`、未対応pathの `error + close`、path間混線なし）。
- 受け入れ条件:
  - `/ws/ticker_usd_jpy` で従来どおり受信できる
  - 未対応pathは `error` + close される
  - path Aのクライアントに path Bのtickerが流れない
  - 新しい通貨ペアpath追加時にコード複製が不要である
- 注意点:
  - `fetch_rows_after(last_processed_time)` の初回 `None` 扱いを明確化する
  - `ClientRegistry.add()` の戻り値型/戻り値の不整合を整理する


## T6: transform.pyを責務単位に分割する。

- USD/JPYにしか対応していない処理を他通貨ペアにも適用する形に修正する。
  - transform.pyファイルを分割する。 **済**
  - 各timeframeのohlc生成関数を共通化する **済**
- 残作業（未完了のみ）:
  - `indicator` フローを `currency_pair_code` でもループさせ、`period x timeframe x currency` で実行されるようにする。
  - `RSI/SMA/EMA_TASK_DEFAULT_PARAMS` の `currency_pair_code = "USD/JPY"` 固定を見直す（単体実行時の多通貨対応）。
  - `update_ema_task` の `ema_params=None` 時の扱いを `build_ema_params()` で他タスクと同等に統一する。
  - strategy（golden/dead cross）で通貨ペア/時間足スコープを明示的に指定できるようにする（`timeframe` TODO の解消）。


## T7: CI整備（壊れたら即検知）

- 内容:
  - `lint + pytest` を自動実行するCI（例: GitHub Actions）を追加する。
- 工数目安:
  - 半日
- 完了条件:
  - PR/pushでテスト結果が自動で確認できる。


## T8: transform系の最小受け入れテスト

- 内容:
  - OHLC / indicator / strategy のスモークテストを追加する。
  - 多通貨1ケース（`USD/JPY`以外を含む）を追加する。
  - 再実行安全性（重複挿入されないこと）を確認する。
- 工数目安:
  - 1〜2日
- 完了条件:
  - 主要フローの最低限テストが通る。


## T9: 設定の外部化（最小）

- 内容:
  - 通貨ペア・時間足・period を環境変数で上書き可能にする。
- 工数目安:
  - 半日〜1日
- 完了条件:
  - `config.py` 固定値に依存せず実行パラメータを切り替えできる。


## T10: 性能対策（計測ベース）

- 内容:
  - `EXPLAIN ANALYZE` で遅いクエリを特定する。
  - 実測結果に基づき必要最小限のインデックスを追加する。
- 工数目安:
  - 1日
- 完了条件:
  - ボトルネッククエリの実測改善を確認できる。


## T11: データ保持方針の実装

- 内容:
  - ticker生データの保持期間を定義する。
  - 集約後データのアーカイブ/削除ルールを定義して実装する。
- 工数目安:
  - 半日
- 完了条件:
  - 保持・削除ルールがSQLまたは運用手順として固定される。


## T12: DBマイグレーション管理導入

- 内容:
  - Alembic等を導入し、DDL変更を履歴管理する。
- 工数目安:
  - 1〜2日
- 完了条件:
  - 新規のスキーマ変更がマイグレーション経由で適用できる。


## T13: 運用監視・アラート

- 内容:
  - フロー失敗率、遅延、最終更新時刻を可視化する。
  - 閾値超過時の通知を追加する。
- 工数目安:
  - 1日〜
- 完了条件:
  - 異常時に自動検知・通知できる。


## 進捗記録

### T1: 完了

### T2: 完了

### T3: 完了

### T4: 完了

### T5: 進行中

### T6: 進行中

### T7: 未着手

### T8: 未着手

### T9: 未着手

### T10: 未着手

### T11: 未着手

### T12: 未着手

### T13: 未着手

