INSERT INTO usd_jpy_1m (time, open, high, low, close)
SELECT
bucket AS time,
(array_agg(bid ORDER BY time))[1] AS open,
MAX(bid) AS high,
MIN(bid) AS low,
(array_agg(bid ORDER BY time DESC))[1] AS close
FROM (
    SELECT
        DATE_TRUNC('minute', time) AS bucket,
        time,
        bid
    FROM ticker_usd_jpy
     ) d
GROUP BY bucket
ON CONFLICT DO NOTHING;

-- CTE版(こっちのほうが好み)
INSERT INTO usd_jpy_1m (time, open, high, low, close)
WITH bucket_time AS (
SELECT
    DATE_TRUNC('minute', time) AS bucket,
    time,
    bid
FROM ticker_usd_jpy
)
SELECT
bucket AS time,
(array_agg(bid ORDER BY time))[1] AS open,
MAX(bid) AS high,
MIN(bid) AS low,
(array_agg(bid ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;



INSERT INTO usd_jpy_5m (time, open, high, low, close)
WITH bucket_time AS (
SELECT
    date_trunc('minute', time) - (EXTRACT(minute FROM time)::int % 5) * interval  '1 minute' AS bucket,
    time,
    open,
    high,
    low,
    close
FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY time))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;

INSERT INTO usd_jpy_30m (time, open, high, low, close)
WITH bucket_time AS (
SELECT
    date_trunc('minute', time) - (EXTRACT(minute FROM time)::int % 30) * interval  '1 minute' AS bucket,
    time,
    open,
    high,
    low,
    close
FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY time))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;


INSERT INTO usd_jpy_1h (time, open, high, low, close)
WITH bucket_time AS (
    SELECT
        date_trunc('hour', time) AS bucket,
        time,
        open,
        high,
        low,
        close
    FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY time))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;


INSERT INTO usd_jpy_4h (time, open, high, low, close)
WITH bucket_time AS (
    SELECT
        date_trunc('hour', time) - (EXTRACT(hour FROM time)::int % 4) * interval '1 hour' AS bucket,
        time,
        open,
        high,
        low,
        close
    FROM usd_jpy_1m
)
SELECT
    bucket AS time,
    (array_agg(open ORDER BY time))[1] AS open,
    MAX(high) AS high,
    MIN(low) AS low,
    (array_agg(close ORDER BY time DESC))[1] AS close
FROM bucket_time
GROUP BY bucket
ON CONFLICT DO NOTHING;





