# tasks in commonize branch

このドキュメントは、為替データの受信を行う`ws-connection.py`と、
その情報をDBに蓄積し、分析を行う`etl/*`の処理を段階的に実装するための作業計画である。

## USD_JPY以外の通貨ペアにも対応する
- dim_currencyに存在する通貨ペアについて、
  - ticker_{CURRENCY_PAIR_CODE} テーブルを生成する
  - {CURRENCY_PAIR_CODE}_{TIMEFRAME_CODE} テーブルを生成する


## ws-connection.py

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


