CREATE TABLE IF NOT EXISTS fact_rsi (
    time TIMESTAMP NOT NULL,
    currency_id INTEGER NOT NULL REFERENCES dim_currency(id),
    timeframe_id INTEGER NOT NULL,
    period INTEGER NOT NULL,
    calc_version TEXT NOT NULL,
    value NUMERIC(10, 4),
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (time, currency_id, timeframe_id, period, calc_version)
);