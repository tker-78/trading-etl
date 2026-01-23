# Trading Application 設計整理（全体像）

**この設計書はChatGPT5.2で自動生成しました**

## 1. 目的と設計方針

本アプリケーションは、為替取引（アルゴリズムトレード）において **リアルタイム処理・取引管理・分析（BI）** を明確に分離し、

* リアルタイム性
* 分析再現性
* 将来拡張性（指標追加・時間軸追加）

を同時に満たすことを目的とする。

設計の中核思想は以下の通り。

* **Realtime / Transaction / Analytics を物理的・論理的に分離する**
* **粒度（grain）を意識した DWH 設計を行う**
* **UI はデータ取得方法を知らない（責務分離）**

---

## 2. 全体アーキテクチャ概要

### 構成要素

* Python Backend
* RealtimeDB
* TransactionDB
* DWH
* UI（Streamlit + Plotly）
* BI（Apache Superset）

---

## 3. データフローと責務分担

### 3.1 Python Backend

* GMO Coin WebSocket から Tick データを受信
* Tick を 1min OHLC に整形
* トレードロジックを実行
* 以下の DB への書き込みを担当

  * RealtimeDB（OHLC）
  * TransactionDB（取引・ポジション）

Backend は **唯一の業務ロジック実行点** であり、UI や BI はロジックを持たない。

---

### 3.2 RealtimeDB

#### 役割

* 高頻度・短期データの保持
* UI によるリアルタイム可視化のためのデータ供給

#### データ内容

* 1min OHLC（最小粒度）
* Tick データは保持しない、または TTL 付きで限定保持

#### ポリシー

* 指標計算は行わない
* 長期保存を前提としない

---

### 3.3 TransactionDB

#### 役割

* 取引実行結果の正としての永続化

#### データ内容

* 注文
* 約定
* ポジション
* 損益（PnL）

#### 特徴

* 会計・監査的観点での正
* DWH への ETL 元データ

---

### 3.4 DWH（Data Warehouse）

#### 役割

* 分析・検証・BI 用データの集約
* 再現可能な分析基盤

#### データ投入元

* RealtimeDB → 集約 OHLC + 指標
* TransactionDB → 取引実績

#### モデリング方針

* Kimball 型（Star Schema）

##### Dimension

* Dim_date
* Dim_currency
* Dim_timeframe
* Dim_indicator
* Dim_strategy（必要に応じて）

##### Fact

* Fact_ohlc

  * grain: (date, currency, timeframe)
  * measures: open, high, low, close, volume

* Fact_indicator

  * grain: (date, currency, indicator)
  * measures: value

* Fact_trade_result

  * grain: (trade_id)
  * measures: pnl, duration, slippage

※ 上昇率などの派生値は、必要に応じて Fact として定義する。

---

## 4. ETL 方針

### RealtimeDB → DWH

* 1min OHLC を入力
* 1h / 4h / 1d / 1w OHLC を再集約
* インジケータを計算
* 再現可能な定義（window, parameter）をメタデータとして保持

### TransactionDB → DWH

* 取引履歴を分析用 Fact に変換
* 日次・戦略別・通貨別の集計を実施

---

## 5. UI / BI レイヤ

### 5.1 UI（Streamlit + Plotly）

* 役割: 可視化専用
* Backend API 経由でデータ取得
* DB スキーマを直接参照しない
* リアルタイム OHLC・現在ステータス表示

### 5.2 BI（Apache Superset）

* DWH のみを参照
* 過去検証・戦略評価・傾向分析を担当
* リアルタイム性は求めない

---

## 6. 設計上の重要ポイント（まとめ）

* Realtime / Transaction / Analytics を混ぜない
* 粒度（grain）を壊さない
* UI は取得方法を知らない
* Backend が意味論の唯一の責務点
* DWH は「分析の正」として再現性を最優先する

以上の設計により、

* 個人開発でも破綻しない
* 分析・改善が回る
* 将来的な拡張（指標・時間軸・戦略追加）が容易

なトレーディングアプリケーションを実現する。
