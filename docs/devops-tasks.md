## DevOps Tasks Index

提案したブランチ境界に合わせ、`T8〜T13` は1タスク=1ドキュメントに分割。

## T7: CI整備（壊れたら即検知）

- 内容:
    - `lint + pytest` を自動実行するCI（例: GitHub Actions）を追加する。
- 具体作業:
    1. `lint` ツールを決める（例: `ruff`）。
    2. 開発用依存を追加する（例: `requirements-dev.txt` に `ruff`, `pytest`）。
    3. ローカル実行コマンドを固定する（例: `ruff check .` / `pytest -q`）。
    4. `pytest` が0件で落ちないように最小スモークテストを追加する（例: `tests/test_smoke.py`）。
    5. `.github/workflows/ci.yml` を作成し、`push` / `pull_request` で `lint + pytest` を実行する。
    6. ブランチをpushしてGitHub Actionsの実行結果を確認する。
    7. PR画面でCIステータスが確認できることを確認する。
- 工数目安:
    - 半日
- 完了条件:
    - PR/pushでテスト結果が自動で確認できる。
- 受け入れチェック:
    - `push` と `pull_request` の両方でCIが起動する。
    - `lint` と `pytest` の結果がGitHub上で確認できる。
    - 失敗時にCIが即時失敗として表示される。

## T8〜T13（分割済み）

- T8: [`docs/devops-tasks/t8-transform-tests.md`](docs/devops-tasks/t8-transform-tests.md)
  - 推奨ブランチ: `feature/t8-transform-tests`
- T9: [`docs/devops-tasks/t9-config-env.md`](docs/devops-tasks/t9-config-env.md)
  - 推奨ブランチ: `feature/t9-config-env`
- T10: [`docs/devops-tasks/t10-performance-index.md`](docs/devops-tasks/t10-performance-index.md)
  - 推奨ブランチ: `feature/t10-performance-index`
- T11: [`docs/devops-tasks/t11-retention-policy.md`](docs/devops-tasks/t11-retention-policy.md)
  - 推奨ブランチ: `feature/t11-retention-policy`
- T12: [`docs/devops-tasks/t12-migration-alembic.md`](docs/devops-tasks/t12-migration-alembic.md)
  - 推奨ブランチ: `feature/t12-migration-alembic`
- T13: [`docs/devops-tasks/t13-monitoring-alert.md`](docs/devops-tasks/t13-monitoring-alert.md)
  - 推奨ブランチ: `feature/t13-monitoring-alert`

## 依存メモ

- `T10`（性能対策）は `T12`（マイグレーション管理）と依存しやすいため、`T12` を先行または同時進行推奨。


## 進捗記録

### T7: 完了

### T8: 未着手

### T9: 未着手

### T10: 未着手

### T11: 未着手

### T12: 未着手

### T13: 未着手
