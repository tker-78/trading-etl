# USD/JPY Ticker WebSocket 仕様

## 1. 目的

`ticker_usd_jpy` のリアルタイム価格を UI に配信するための、
サーバー・クライアント間 WebSocket 契約を定義する。

## 2. エンドポイント

- URL: `/ws/ticker_usd_jpy`
- Protocol: `ws` / `wss`
- 方向:
  - クライアント -> サーバー: 送信なし（購読不要）
  - サーバー -> クライアント: `ticker` / `heartbeat` / `error`

## 3. 共通フォーマット

すべてのメッセージは JSON オブジェクトとし、`type` を必須とする。

```json
{
  "type": "ticker | heartbeat | error"
}
```

## 4. イベント定義

### 4.1 ticker

最新価格を通知するイベント。

必須項目:
- `type`: `"ticker"`
- `symbol`: `"USD_JPY"`
- `bid`: number
- `ask`: number
- `mid`: number (`(bid + ask) / 2`)
- `timestamp`: string (ISO 8601, UTC。例: `2026-02-16T13:05:10.123Z`)

例:

```json
{
  "type": "ticker",
  "symbol": "USD_JPY",
  "bid": 151.245,
  "ask": 151.249,
  "mid": 151.247,
  "timestamp": "2026-02-16T13:05:10.123Z"
}
```

### 4.2 heartbeat

接続維持と死活監視のためのイベント。

必須項目:
- `type`: `"heartbeat"`
- `timestamp`: string (ISO 8601, UTC)

例:

```json
{
  "type": "heartbeat",
  "timestamp": "2026-02-16T13:05:30.000Z"
}
```

### 4.3 error

配信継続可能なエラー通知イベント。

必須項目:
- `type`: `"error"`
- `code`: string
- `message`: string
- `timestamp`: string (ISO 8601, UTC)

例:

```json
{
  "type": "error",
  "code": "UPSTREAM_DISCONNECTED",
  "message": "upstream feed disconnected",
  "timestamp": "2026-02-16T13:06:00.001Z"
}
```

## 5. サーバー動作ルール

- `heartbeat` は 30 秒間隔で送信する。
- 新規接続直後に、キャッシュ済みの最新 `ticker` があれば 1 件即時送信する。
- 無効な価格（`bid <= 0`、`ask <= 0`、`bid > ask`）は破棄する。
- タイムスタンプは UTC の ISO 8601（末尾 `Z`）で配信する。

## 6. クライアント実装ルール

- `type` を見てイベントを振り分ける。
- `ticker` 未受信が 5 秒以上継続した場合は stale 警告表示を行う。
- 切断時は指数バックオフで再接続する（例: 1s, 2s, 4s, 8s, max 30s）。

## 7. 後方互換ポリシー

- 追加項目は後方互換とみなす（既存項目の意味は変更しない）。
- 既存必須項目の削除・型変更はメジャー互換性破壊とする。
