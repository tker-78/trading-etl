# Dimensional modeling

## dimension tables



## fact tables

### 1. fact_ohlc

- ストーリー: 為替の基本情報としてローソク足情報を知りたい
- 粒度: currency x timeframe

### 2. fact_rsi

- ストーリー: 
- 粒度: currency x timeframe x time x parameter
- 指標: RSIの値


- sample query:

```sql
CREATE TABLE IF NOT EXISTS fact_rsi (
    time_key TIMESTAMP NOT NULL,
    currency_id INTEGER NOT NULL,
    timeframe_id INTEGER NOT NULL,
    period INTEGER NOT NULL,
    calc_version TEXT NOT NULL,
    value NUMERIC(10, 4),
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (time_key, currency_id, timeframe_id, period, calc_version)
);
```


```sql
SELECT
    f.currency_key,
    f.timeframe_key,
    t.time,
    parameter, # pythonで指定
    rsi_value # talibで計算
FROM fact_ohlc f 
LEFT JOIN dim_currency c ON f.currency_id = c.id
LEFT JOIN dim_timeframe tf ON f.timeframe_id = tf.id
LEFT JOIN dim_time t ON f.time = t.time;
```