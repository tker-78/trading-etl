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
GROUP BY bucket;