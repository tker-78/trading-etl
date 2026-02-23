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



## T4: ws-connection.py

- 各種通貨ペア毎のクラス、ticker_factoryの生成を共通化する。
- dim_currencyの`currency_pair_symbol`を取得して、動的にクラスを生成する、または
  動的に


## T5: transform.pyを責務単位に分割する。

- 


## 進捗記録

### T1: 完了

### T2: 完了

### T3: 進行中

### T4: 未着手

### T5: 未着手







