# Alembic

このレポジトリでは`Alembic`を使ってマイグレーション管理を行います。

## 使い方

```
docker compose run --rm alembic alembic init migrations # 初回のみ
docker compose run --rm alembic alembic upgrade head # 最新の状態に更新
docker compose run --rm alembic alembic downgrade base # 初期状態に戻す
```

```
docker compose run --rm alembic alembic revision <revision_name> # マイグレーションファイルを生成する
```

## 注意点

ohlcテーブル(ローソク足)は、ETLで`dim_currency`, `dim_timeframe`に基づき動的に生成しています。
そのため、ohlcテーブルはalembicで管理しません。
