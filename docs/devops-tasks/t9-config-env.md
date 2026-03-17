## T9: 設定の外部化（最小）

- 推奨ブランチ: `feature/t9-config-env`
- 内容:
    - 通貨ペア・時間足・period を環境変数で上書き可能にする。
- 工数目安:
    - 半日〜1日
- 完了条件:
    - `config.py` 固定値に依存せず実行パラメータを切り替えできる。

## 着手条件

- [x] 現行の設定読み込み箇所（通貨ペア・時間足・period）を特定できている。
- [x] 環境変数名とデフォルト値の方針が合意されている。
- [x] 既存フローに影響する破壊的変更（未設定時の挙動変更）がない設計になっている。

## Done定義

- [x] 通貨ペア・時間足・period が環境変数で上書き可能。
- [x] 環境変数未設定時は既存デフォルト値で従来どおり動作する。
- [x] 不正値入力時の挙動（エラーまたはフォールバック）が明確で、テストで確認できる。
- [x] 設定方法がドキュメント化されている。

## 実装メモ

- 読み込み箇所: `src/config/config.py`
- 使用する環境変数:
  - `DEFAULT_CURRENCY_PAIR_CODE`
  - `DEFAULT_TIMEFRAME_CODE`
  - `DEFAULT_PERIOD`
  - `DEFAULT_PERIODS`
  - `DEFAULT_TIMEFRAMES`
- 未設定時は既存デフォルト値を使用する。
- 不正値が設定されている場合は `ValueError` を送出し、起動時に明示的に失敗させる。
- 検証テスト: `tests/config/test_config.py`

## 検証コマンド

- `ruff check .`
- `pytest -q`
- `pytest -q tests -k "config or env"`
