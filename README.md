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

supersetの起動

```bash
docker compose -f superset/docker-compose-image-tag.yml up -d
```

supersetから`etl-db`を参照するには、networkのconnectが必要。

```bash
docker network connect superset_default trading-etl-etl-db-1
```
