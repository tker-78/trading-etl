# 分析要件

1. OHLCをもとにして、各種インジケーターを計算、表示できる。
2. 分析に用いるOHLCデータにリアルタイム性は求めない
   - 各時間足の行が確定した段階で書き込まれればOK
3. talibで使用できる分析関数のうち、下記を使用する
4. 分析結果は`analysis`データベースに格納する。
5. 分析結果は分析指標毎に`fact_<分析指標名>`テーブルに保存する。


## ユーザーストーリー

1. 為替トレードのバックテストを行う。
2. どんな分析？ -> インジケーターの分析結果を用いて、イベント駆動のバックテストを行う。
3. つまり？ -> インジケーターの値にしきい値を設けて、それをListenして、売買イベントのトリガーとする。
4. たとえば？ -> SMAの短期が長期に対するゴールデンクロスになったら買いイベント、デッドクロスで売りイベントなど。
5. そのイベントはどう扱う？ -> fact_buysell_eventsとして保存する。
6. それはどう使うの？ -> fact_buysell_eventsには売買のトリガの情報を(fact_rsiのキーなど)を持つので、fact_buysell_eventsを参照すれば
   売買の情報を取得できる。つまり、バックテストのパフォーマンス分析はこのテーブルを起点に行える。
7. fact_buysell_eventsはどうやって売買トリガを持つの？ -> 下記のスキーマを想定している。
   ```sql
   CREATE TABLE IF NOT EXISTS fact_buysell_events
   (
       event_id    SERIAL PRIMARY KEY,
       symbol      VARCHAR(10) NOT NULL, -- e.g. USD/JPY
       event_type  VARCHAR(10) NOT NULL, -- buy or sell
       event_time  TIMESTAMPTZ NOT NULL,
       event_price NUMERIC(10),
       event_trigger_key VARCHAR(100) NOT NULL -- e.g. rsi_14
   );
   ```
8. event_trigger_keyをテキストで持つのは、バックエンド処理が増えるよね？ -> うん。多分そう。
9. indicatorのfactテーブルが多数あるなら、そのカラムをfact_buysell_eventsに最初からすべて用意しないといけないんじゃない？ -> どうだろ？わからん。

**改善後のfact_buysell_events**
```sql
CREATE TABLE IF NOT EXISTS fact_buysell_events (
    event_id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    event_type VARCHAR(10) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    event_price FLOAT,
    trigger_indicator_name VARCHAR(50) NOT NULL,
    trigger_indicator_value FLOAT,
    trigger_indicator_time TIMESTAMP
);
```
    




