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
- transform.pyファイルを分割する。


## 進捗記録

### T1: 完了

### T2: 完了

### T3: 完了

### T4: 完了

### T5: 進行中

### T6: 進行中



