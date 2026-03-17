# Trading ETL

このアプリケーションは、為替トレードを題材にプロダクションレベルのETL処理の構築を行っています。

## 使用する技術

- Python
- Prefect
- Superset
- Vue.js
- Docker
- PostgreSQL

## 実行方法

```bash
docker compose up -d
```

設定は `.env` またはシェル環境変数で上書きできる。未設定時は既存デフォルト値を使う。

```bash
export DEFAULT_CURRENCY_PAIR_CODE=EUR/JPY
export DEFAULT_TIMEFRAME_CODE=5m
export DEFAULT_PERIOD=21
export DEFAULT_PERIODS=7,21,42
export DEFAULT_TIMEFRAMES=5m,15m,1h
```

利用可能な主な設定値:

- `DEFAULT_CURRENCY_PAIR_CODE` 既定値: `USD/JPY`
- `DEFAULT_TIMEFRAME_CODE` 既定値: `1m`
- `DEFAULT_PERIOD` 既定値: `14`
- `DEFAULT_PERIODS` 既定値: `14,28,56`
- `DEFAULT_TIMEFRAMES` 既定値: `1m,5m,30m,1h,4h`

不正値の扱い:

- `DEFAULT_PERIOD` は整数のみ許可
- `DEFAULT_PERIODS` はカンマ区切り整数のみ許可
- `DEFAULT_CURRENCY_PAIR_CODE` / `DEFAULT_TIMEFRAME_CODE` / `DEFAULT_TIMEFRAMES` は空文字不可
- 不正値が設定されている場合は `src.config.config` 読み込み時に `ValueError` で停止する


supersetの起動

```bash
docker compose -f superset/docker-compose-image-tag.yml up -d
```

supersetから`etl-db`を参照するには、networkのconnectが必要。

```bash
docker network connect superset_default trading-etl-etl-db-1
```

## WebSocket UI (T4 PoC)

DockerでWebSocketサーバーとUI静的配信を同時に起動する。

```bash
docker compose up -d ws-ticker-server ui-server
```

`ws-ticker-server` は `8765:8765` を公開し、`ui-server` は `8080:8080` を公開する。
ブラウザで `http://localhost:8080/ticker_usd_jpy.html` を開く。



## テスト

```bash
# テスト環境を起動
docker compose --profile test up -d
```

```bash
pytest -q
pytest -q tests -k "config or env"
```

