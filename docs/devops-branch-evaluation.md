# @devops ブランチ設計レビュー（2026-03-13）

## 総合評価
- **78 / 100**
- 評価対象: `docs/devops-tasks.md` と `docs/devops-tasks/T8〜T13` のブランチ分割設計

## 良い点（加点）
1. **1タスク=1ブランチの粒度が明確**
   - `feature/t8-*`〜`feature/t13-*` に分ける方針で、レビュー対象が小さくなっている。
2. **Done定義・着手条件が揃っている**
   - 各タスクに「着手条件」「Done定義」「検証コマンド」があり、進捗判定しやすい。
3. **依存関係の明示がある**
   - `T10` と `T12` の依存メモが書かれており、順序設計の意識がある。

## 課題（減点）
1. **依存関係が最小限で、実運用の順序制御としては弱い**
   - 主要依存（例: `T8`→`T9`→`T12`→`T10`→`T11`→`T13`）が明文化されていない。
2. **マージ戦略が未定義**
   - squash/rebase方針、ブランチ保護、必須チェック、レビュー人数などの規約がない。
3. **CIゲートの品質要件が不足**
   - `ruff`/`pytest` はあるが、`coverage`、`migration check`、`docker compose` のヘルス確認がない。
4. **運用系タスクの検証観点が抽象寄り**
   - `T11/T13` は実装後の「再現可能な検証手順（fixture/サンプル負荷）」まで落ちていない。

## 推奨ブランチ実行順（改善案）
1. `feature/t8-transform-tests`
2. `feature/t9-config-env`
3. `feature/t12-migration-alembic`
4. `feature/t10-performance-index`
5. `feature/t11-retention-policy`
6. `feature/t13-monitoring-alert`

> 理由: 先にテストと設定外部化を固め、DDL管理を入れてから性能調整・運用施策へ進むと、手戻りが最小化される。

## すぐ追加すべき運用ルール
- PRテンプレートに以下を必須化
  - 変更対象（コード/DDL/運用）
  - ロールバック手順
  - 計測結果（Before/After）
- ブランチ保護
  - 必須: `ruff check .` / `pytest -q`
  - 推奨: migrationの往復確認（`upgrade`/`downgrade`）
- タスク完了時の証跡
  - `docs/devops-tasks.md` に完了日、PR番号、実測ログへのリンクを追記

## 90点に上げるための最短アクション
- `docs/devops-tasks.md` に **依存DAG** と **推奨マージ順** を追記
- `T12` に「CIで migration dry-run」を Done条件として追加
- `T10` に「対象クエリ一覧テンプレート（SQL + 期待SLA）」を追加
- `T13` に「アラート誤検知率の評価期間」を追加

---
この設計は「分割の基本」はできており、**実行統制（依存・ゲート・証跡）を補強すれば即戦力レベル**になります。
