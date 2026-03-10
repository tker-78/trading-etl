## T12: DBマイグレーション管理導入

- 推奨ブランチ: `feature/t12-migration-alembic`
- 内容:
    - Alembic等を導入し、DDL変更を履歴管理する。
- 工数目安:
    - 1〜2日
- 完了条件:
    - 新規のスキーマ変更がマイグレーション経由で適用できる。

## 着手条件

- [ ] 現行DDLの管理方法（手動SQLなど）を棚卸しできている。
- [ ] マイグレーション対象DB接続情報が確定している。
- [ ] マイグレーション命名規約・運用ルール（作成/適用/レビュー）が合意されている。

## Done定義

- [ ] Alembic（または同等ツール）が導入され、初期設定がリポジトリに含まれている。
- [ ] 少なくとも1本のマイグレーションを作成し、`upgrade` / `downgrade` の往復が確認できる。
- [ ] 新規スキーマ変更をマイグレーション経由で適用できることを確認した。
- [ ] 開発者向け実行手順がドキュメント化されている。

## 検証コマンド

- `ruff check .`
- `pytest -q`
- `alembic current`
- `alembic upgrade head`
- `alembic downgrade -1`

## 適用順序・手順（実装方針）

### 1. 現状棚卸し（対象定義）

- DDL対象を確定する。
  - `etl/sql/create_*.sql`
  - `etl/flows/transform_services.py` 内の `CREATE TABLE`
- 管理責務を分離する。
  - Alembic: DDL（CREATE/ALTER/DROP, 制約, index）
  - ETL: 日常実行DML（集計INSERT/UPSERT）
- 対象のSQLファイル:
  - create_dimensions.sql
  - create_fact_buysell_events.sql
  - create_fact_ema.sql
  - create_fact_rsi.sql
  - create_fact_sma.sql
  - insert_dimensions.sql

### 2. 接続設定の確定

- Alembicの接続先を統一する（`alembic.ini` または `alembic/env.py`）。
- 開発/本番での適用経路（ローカル, CI/CD）を決める。

### 3. Baseline（初期リビジョン）作成

- 現在の本番相当スキーマを初期リビジョンとして固定する。
- 初期リビジョンに含める対象を明記する。
  - schema
  - 各種テーブル
  - 制約/索引
  - 必要なら初期マスタデータ（`dim_currency`, `dim_timeframe`）
- `upgrade` で再現可能、`downgrade` 方針も定義する。

### 4. 運用ルールの確定

- 今後のDDL変更は Alembic 経由のみとする。
- アプリ側での新規 `CREATE TABLE IF NOT EXISTS` 追加は原則禁止する。
- リビジョン命名規約、レビュー観点（破壊的変更、ロールバック可否）を固定する。

### 5. 検証

- `alembic current`
- `alembic upgrade head`
- `alembic downgrade -1`（必要なら `base` まで）
- `ruff check .`
- `pytest -q`

### 6. ドキュメント化

- 開発者向けに以下を明記する。
  - マイグレーション作成手順
  - 適用手順（upgrade）
  - 巻き戻し手順（downgrade）
  - 責務分離（DDLはAlembic、DMLはETL）

### 7. 次段階（単一OHLC化を行う場合）

- Baseline確立後に別リビジョンとして段階移行する。
- 旧構成との併用期間、データ移行、切替手順を事前に定義する。
