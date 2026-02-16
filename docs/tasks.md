# 設計改善タスク(2026/02/16) 

transform.py の設計改善案（実装なし）を、効果が大きい順で提案します。

  1. 責務をファイル分割する（最優先）

  - 現状は 1 ファイルに「SQL生成」「指標計算」「戦略」「Prefect task/flow」が同居しています（etl/flows/transform.py:59, etl/flows/transform.py:190, etl/flows/transform.py:432,
    etl/flows/transform.py:567）。
  - 改善案:
      - ohlc_updater.py（足生成）
      - indicator_service.py（RSI/SMA/EMA 共通計算）
      - strategy_service.py（売買シグナル）
      - transform_flow.py（Prefect task/flow のみ）
  - 効果: 変更影響範囲が小さくなり、テスト単位も明確になります。

  2. RSI/SMA/EMA の重複を「共通パイプライン化」

  - update_rsi/update_sma/update_ema は取得→計算→insert がほぼ同形です（etl/flows/transform.py:190, etl/flows/transform.py:272, etl/flows/transform.py:348）。
  - 改善案:
      - 「対象データ取得」「指標関数適用」「fact insert」を共通化し、指標差分だけを差し替える設計にする。
  - 効果: バグ修正・仕様変更（再計算範囲やcalc_version等）が1箇所で済みます。

  3. SQLをコードから分離し、テンプレート管理

  - 長いSQLが関数内文字列として散在しています（例: etl/flows/transform.py:60, etl/flows/transform.py:441）。
  - 改善案:
      - sql/ 配下にクエリを分離し、名前付きで呼ぶ（ohlc_1m.sql など）。
  - 効果: SQLレビュー性向上、差分追跡容易、ロジックの見通し改善。

  4. ハードコードされた銘柄・時間足を設定駆動に統一

  - OHLC更新が usd_jpy 固定関数になっています（etl/flows/transform.py:59 以降）。
  - 改善案:
      - currency_pair_code, timeframe_code, source table を設定から展開してループ実行する。
  - 効果: 通貨ペア追加時に関数追加不要、スケールしやすい設計になります。

  5. パラメータを dict から型付きオブジェクトへ

  - 多数の dict | None と **params で受け渡し（etl/flows/transform.py:593, etl/flows/transform.py:624）。
  - 改善案:
      - dataclass / pydantic で task引数を型定義。
  - 効果: 実行時エラーの予防、IDE補完、設定不整合の早期検出。

  6. Task/Flow層は「オーケストレーション専用」にする

  - task内で接続ロード＋業務ロジック実行が混在（etl/flows/transform.py:567 以降）。
  - 改善案:
      - taskは「入力を受けて service 呼び出し」だけにし、DB接続管理は共通ラッパで統一。
  - 効果: 再利用性向上、接続/リトライ方針の一元管理。

  7. 戦略クエリにドメイン境界（銘柄・時間足）を明示

  - ゴールデンクロス/デッドクロスは TODO のまま境界指定が弱いです（etl/flows/transform.py:436, etl/flows/transform.py:440）。
  - 改善案:
      - 戦略入力として currency_id/timeframe_id/period pair を明示し、クエリで必ず絞る。
  - 効果: 意図しない全銘柄・全時間足処理を避けられます。

  8. ON CONFLICT DO NOTHING 依存を見直し、再計算戦略を設計化

  - ほぼ全insertが DO NOTHING です（例: etl/flows/transform.py:77, etl/flows/transform.py:268）。
  - 改善案:
      - 「再計算時は上書きするか」「calc_versionで共存するか」を明文化し、upsert方針を統一。
  - 効果: データ整合性・バックフィル運用が安定します。

  補足（設計観点で気になった点）

  - insert_golden_cross_task が引数を受けても未使用です（etl/flows/transform.py:609）。
  - update_ema_task はデフォルト None のまま **ema_params 展開しており、設計上不整合です（etl/flows/transform.py:624）。
    どちらも「API契約を型で固定する」ことで防ぎやすくなります。


› 結構多いね。。今の設計・実装は全然だめってこと？


• だめではないです。
  今の実装は「まず動かす」段階としては十分成立しています。

  現状の強みもあります。

  - 指標ごとの処理が明確で追いやすい
  - Prefectのflow/taskで実行単位が切れている
  - ON CONFLICT DO NOTHING で再実行耐性がある程度ある

  改善提案が多く見えたのは、主に「将来の拡張（銘柄追加・戦略追加・再計算運用）」に備えるときの論点を広めに挙げたためです。
  優先度を絞るなら、まずはこの2つだけで十分です。

  1. RSI/SMA/EMAの重複共通化
  2. ファイル分割（flow と計算ロジックの分離）

  この2つで保守性はかなり上がります。



