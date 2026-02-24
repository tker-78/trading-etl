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

- 各通貨ペア毎に、websocketの配信pathを設ける。
- 実装方針は「1つのWebSocketサーバで複数pathを受ける」構成とする（例: `/ws/ticker_usd_jpy`, `/ws/ticker_eur_jpy`）。
- まずはpath別で実装し、subscribe方式への移行は将来タスクとする。
- `path -> {symbol, table}` の設定マップを導入し、`WS_PATH` / `SYMBOL` の単一固定をやめる。
- `registry` / `latest_ticker` を単一グローバルから、path単位（またはsymbol単位）の辞書で管理する。
- `handler()` で `client.request.path` を設定マップにルーティングし、未対応pathは既存どおり `1008` でcloseする。
- 接続成功時は、該当pathの最新tickerキャッシュのみを初回送信する。
- `handler()` の path ルーティング実装方針（詳細）:
  - 目的は、接続してきたclientの `request.path` から対象通貨ペアを判定し、そのpath専用の state（registry / cache）に紐づけること。
  - `path -> stream config` の辞書（例: `PATH_CONFIG_BY_PATH`）を用意し、`list` ではなく辞書lookupで `symbol` / `table` を同時に取得できるようにする。
  - 処理フロー:
    - `path = client.request.path` を取得する
    - `config = PATH_CONFIG_BY_PATH.get(path)` でルーティングする
    - `config is None` の場合は `send_error_and_close(..., "unsupported path: ...")` を返し、`1008` closeして終了する
    - `config` がある場合は、そのpath用の `registry` / `latest_cache` を選択する
    - clientをそのpath用registryに追加する
    - 該当pathの最新ticker cacheがあれば初回送信する
    - `await client.wait_closed()` で接続終了まで待機する
    - `finally` でそのpath用registryからclientを削除する
  - `handler()` でやること:
    - pathの妥当性判定
    - pathごとのstate選択
    - 接続/切断管理
    - 初回キャッシュ送信
  - `handler()` でやらないこと:
    - DBポーリング
    - ticker生成/整形
    - heartbeat全体制御
  - 実装時の注意:
    - `path` は文字列、許可済みpathが `list` の場合は `path not in path_list` で判定する（`path != path_list` は常に不一致になる）
    - `registry` / `latest_ticker` を単一のまま使うと複数pathで混線するため、必ずpath単位で選択する
  - ログ（推奨）:
    - 接続時: `path`, `symbol`, 接続数
    - 切断時: `path`, `symbol`, 接続数
    - 拒否時: `path`, 許可済みpath一覧
- `fetch_latest_row()` / `fetch_rows_after()` をテーブル名引数で使えるようにパラメータ化する。
- SQLのテーブル名は設定マップからのみ解決し、任意文字列を直接受けない（SQL組み立ての安全性を担保）。
- `db_relay_loop()` は単一通貨前提をやめ、通貨ペア/pathごとのrelay loop（例: `db_relay_loop_for_stream(config)`）に分割する。
- `run_server()` では、各path分のDB relay taskを `asyncio.gather(...)` で起動する。
- heartbeatは当面「全pathの接続クライアントへ共通送信」とし、path別registryを順番に送る構成にする。
- ログは `path`, `symbol`, 接続数 を含めて出力し、複数通貨配信時の切り分けをしやすくする。
- `gmo/ws_ticker_server_client.py` は後続対応として、接続先pathを切り替えられるようにする（T5本体の必須要件ではない）。

- 実装順（推奨）:
  - 設定マップ追加（まずは `USD_JPY` 1件のみ） **済**
  - `handler()` のpathルーティング化
  - registry/cacheのpath別辞書化
  - DB取得関数のパラメータ化
  - relay loopの複数task化
  - heartbeat/ログ整理
- 受け入れ条件:
  - `/ws/ticker_usd_jpy` で従来どおり受信できる
  - 未対応pathは `error` + close される
  - path Aのクライアントに path Bのtickerが流れない
  - 新しい通貨ペアpath追加時にコード複製が不要である
- 注意点:
  - `fetch_rows_after(last_processed_time)` の初回 `None` 扱いを明確化する
  - `FROM ticker.ticker_usd_jpy` と `FROM ticker_usd_jpy` の表記ゆれを統一する
  - `ClientRegistry.add()` の戻り値型/戻り値の不整合を整理する


## T6: transform.pyを責務単位に分割する。

- 


## 進捗記録

### T1: 完了

### T2: 完了

### T3: 完了

### T4: 進行中

### T5: 未着手





