## T8: transform系の最小受け入れテスト

- 推奨ブランチ: `feature/t8-transform-tests`
- 内容:
    - OHLC / indicator / strategy のスモークテストを追加する。
    - 多通貨1ケース（`USD/JPY`以外を含む）を追加する。
    - 再実行安全性（重複挿入されないこと）を確認する。
- 実装方針（2. 多通貨1ケース）:
    1. テスト対象は `update_ohlc_tables` を主対象にする（多通貨ループの本体）。
    2. `SqlAlchemyConnector.load(...).execute(...)` をモックし、通貨ペアを2件返す:
        - 例: `["USD/JPY", "EUR/JPY"]`
        - 時間足は最小構成（例: `("1m", 60), ("5m", 300)`）を返す。
    3. `update_ohlc_base_tables_task.submit` / `update_ohlc_derived_tables_task.submit` をダミー化して呼び出し履歴を検証する。
    4. 検証観点:
        - `base` が `USD/JPY` と `EUR/JPY` の両方で1回ずつ呼ばれること。
        - `derived` が両通貨で呼ばれること（`1m` 以外の時間足分）。
        - `derived` の `wait_for` が同一通貨の `base_future` を参照していること。
    5. 任意で `create_ohlc_tables` も追加検証し、通貨2件 × 時間足2件で `submit` が4回呼ばれることを確認する。
    6. 実装順はTDDに合わせ、まず failing な最小テストを追加してから実装・修正する。
- 工数目安:
    - 1〜2日
- 完了条件:
    - 主要フローの最低限テストが通る。

## 着手条件

- [ ] `T7` のCI（`ruff` / `pytest`）が有効で、テスト結果をPR上で確認できる。
- [ ] 対象フロー（`update_ohlc_tables` / 必要に応じて `create_ohlc_tables`）の現行挙動を把握できている。
- [ ] 多通貨テストケースの期待値（`USD/JPY` + 非`USD/JPY` 1通貨）が合意されている。

## Done定義

- [ ] OHLC / indicator / strategy の最小スモークテストが追加され、`pytest` で安定して成功する。
- [ ] 多通貨ケース（例: `USD/JPY`, `EUR/JPY`）で `base` / `derived` 呼び出し回数と `wait_for` 依存を検証できる。
- [ ] 再実行安全性（重複挿入されないこと）をテストで担保できる。
- [ ] CI（`push` / `pull_request`）で `ruff` と `pytest` がともに green。

## 検証コマンド

- `ruff check .`
- `pytest -q`
- `pytest -q tests -k "ohlc or indicator or strategy"`
