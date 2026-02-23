# Codexからの評価(2026/02/23)
codex resume 019c87f9-4ac9-73f3-966f-e796bb57dbb8


評価: 67 / 100 点

  設計思想はかなり良いですが、実装レベルでは「責務分離の理想」と「現在のコード構成」にギャップがあります。

  加点ポイント

  - 全体の設計方針が明確です。Realtime / Transaction / Analytics 分離、DWH の grain 意識など、方向性は良いです。docs/design_v2.md:7 docs/design_v2.md:17 docs/design_v2.md:91
  - ETL のオーケストレーションに Prefect を使い、task/flow で分けているのは良い判断です。etl/flows/transform.py:620 etl/flows/transform.py:666
  - 指標計算パラメータを config.py に集約している点は、変更容易性に効いています。etl/flows/config.py:1
  - WebSocket 配信サーバーは registry / cache / DB relay の責務が比較的分かれていて、局所的には設計が良いです。gmo/ws_ticker_server.py:34 gmo/ws_ticker_server.py:52 gmo/
    ws_ticker_server.py:161

  減点ポイント（大きい）

  - ETL の中核ロジックが etl/flows/transform.py に集中しすぎています（集約、指標計算、シグナル生成、Prefect task/flow まで同居）。変更の影響範囲が広くなります。etl/flows/
    transform.py:86 etl/flows/transform.py:217 etl/flows/transform.py:459 etl/flows/transform.py:592
  - 通貨・時間足の拡張性が低いです。USD/JPY 固定の関数群が増殖しており、設計書の「拡張容易」とズレます。etl/flows/transform.py:86 etl/flows/transform.py:108 etl/flows/
    transform.py:133 etl/flows/transform.py:158 etl/flows/transform.py:183
  - DB モデルの一貫性が弱いです。fact_rsi などで timeframe_id が FK でなく、fact_buysell_events は trigger_indicator_timeframe を VARCHAR にしているのに、実装側では timeframe_id
    を入れています（意味論がズレる）。etl/sql/create_fact_rsi.sql:4 etl/sql/create_fact_buysell_events.sql:10 etl/flows/transform.py:518 etl/flows/transform.py:580
  - 設計書では DB を分離する方針ですが、実装は実質単一業務DB寄りです（forex-db に ticker/OHLC/fact が集まる構成）。docs/design_v2.md:17 docker-compose.yaml:2 etl/flows/
    transform.py:61
  - 接続設定が分散・重複しています。database/base.py と etl/db_connection.py に接続情報がハードコードされ、構成管理の一貫性が弱いです。database/base.py:16 etl/db_connection.py:8
  - gmo/ws-connection.py の通貨クラス/ファクトリは手作業定義が多く、しかも実際の ticker_factory は一部しか有効化されていません。gmo/ws-connection.py:76 gmo/ws-connection.py:91

  補足（品質面）

  - テストがほぼ SQL 1件のみで、設計変更の安全性を担保しにくい状態です。etl/sql/test/test_insert_sma_golden_cross.sql

  総評

  - 「構想設計」は強い（80点台）。
  - 「実装設計」はまだ発展途上（50点台）。
  - 現時点の総合としては 67点 が妥当です。


## codexからの改善タスク
codex resume 019c8c1a-a83f-71d2-9f34-37ae1a8e28fc

• 90点に上げるための作業リスト（2時間単位）

  前提: 今の 82/100 から、次の10〜15時間 で 88〜92点 を狙うプランです。
  方針は「新機能追加」より 整理・再現性・検証 を優先します。

  到達イメージ

  - README を見れば第三者でも起動しやすい
  - transform.py の責務が分かれて読める
  - 最低1つのロジックが自動テストで守られている
  - 未完成箇所が「放置」ではなく「管理」されている

  ———

  Phase 1（最優先 / 4時間）

  1. README.md を「最短起動手順」に再構成（2h）

  - 追加する内容:
      - 前提環境（Docker, Python など）
      - 起動コマンド
      - DB初期化手順（必要ならSQL実行順）
      - 動作確認方法（どこを見れば成功か）
      - よくある詰まりポイント
  - 効果:
      - 再現性の点数が一気に上がる
      - 将来の自分が助かる

  2. 未実装箇所の棚卸し（2h）

  - 対象:
      - gmo/apiclient.py
      - core/backtest_engine.py
      - TODO コメント周辺
  - やること:
      - 各ファイル先頭に「目的」「今の状態」「次にやること」をコメント/Docstringで明記
      - docs/tasks.md に優先度付きで登録（P1/P2/P3）
  - 効果:
      - 「未完成」→「計画済み」に変わる
      - 見た目の完成度より、開発運用の質が上がる

  ———

  Phase 2（保守性アップ / 4〜6時間）
  3. etl/flows/transform.py を分割（2h）

  - まずは最小分割で十分:
      - etl/flows/ohlc.py（足生成）
      - etl/flows/indicators.py（RSI/SMA/EMA）
      - etl/flows/strategy.py（売買シグナル）
      - etl/flows/transform.py（Prefect task/flow の入口だけ）
  - 効果:
      - 読みやすさ/保守性がかなり改善
      - 次のテスト追加がやりやすくなる

  4. 明らかな不整合を修正（2h）

  - 例:
      - insert_golden_cross_task が引数未使用
      - update_ema_task の ema_params=None 展開
  - 効果:
      - 実行時エラーの芽を潰せる
      - コード品質の点数を取りやすい

  5. 設定・パラメータの入口を統一（2h, 余力）

  - _build_*_params() の使い方をそろえる
  - デフォルト適用の挙動を RSI/SMA/EMA で統一
  - 効果:
      - 「動くけど不安」状態を減らす

  ———

  Phase 3（テスト最低ライン / 4時間）
  6. pytest 導入 + 1本目のテスト（2h）

  - 最初は小さくて良い:
      - 純関数化できる helper（テーブル名生成など）
      - もしくはシグナル判定ロジックを小関数に切り出してテスト
  - 効果:
      - テスト文化の土台ができる
      - 評価の印象が大きく上がる

  7. 戦略ロジックの回帰テストを1本追加（2h）

  - 既存の etl/sql/test/test_insert_sma_golden_cross.sql を活かす方針でもOK
  - 理想は:
      - 「ゴールデンクロス検知される」
      - 「継続状態では検知されない」
  - 効果:
      - 学習プロジェクトでも「検証できる実装」になる

  ———

  Phase 4（運用品質 / 2〜4時間）
  8. DB接続設定を環境変数化（2h）

  - 対象: database/base.py
  - 例:
      - DATABASE_URL を読む
      - Docker用/ローカル用は .env で切替
  - 効果:
      - 再現性と安全性が上がる
      - ハードコード感が減る

  9. 実行確認コマンドを README に追加（2h, 余力）

  - 例:
      - コンテナ状態確認
      - DBテーブル確認
      - Prefect UI確認
  - 効果:
      - 「動いているか分からない」を減らせる

  ———

  10〜15時間の配分例（現実的）

  1. 2h: README.md 再構成
  2. 2h: 未実装箇所の棚卸し + docs/tasks.md 整理
  3. 2h: transform.py 分割（ファイル作成・移動）
  4. 2h: task/params不整合修正
  5. 2h: pytest 導入 + 1テスト
  6. 2h: 戦略ロジック追加テスト
  7. 2h: DATABASE_URL 環境変数化（余力）
  8. 1h: README最終調整（余力）

  ———

  この期間でやらない方がいいこと

  - 新しい指標を増やす
  - UI を作り込む
  - バックテストを本格実装し始める
  - 設計の全面刷新（やりすぎ）

  理由:

  - 点数を上げる観点では、今は 機能追加 より 整える 方が効くからです。

  ———

  90点ラインの目安（今回の前提）

  - README 再現性: 改善済み
  - transform.py 分割: 実施済み
  - 明確なバグの芽: 修正済み
  - 自動テスト: 最低2本
  - 設計メモと実装のズレ: 最低限整理済み

  ここまでやると、個人学習初期としては かなり強い 状態になります。