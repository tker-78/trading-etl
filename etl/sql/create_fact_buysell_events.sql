CREATE TABLE IF NOT EXISTS fact_buysell_events (
    event_id SERIAL PRIMARY KEY,
    event_datetime TIMESTAMP NOT NULL,
    currency_id INTEGER NOT NULL,
    price FLOAT NOT NULL,
    quantity INTEGER NOT NULL,
    event_type VARCHAR(10) NOT NULL, -- e.g. buy or sell
    trigger_indicator_name VARCHAR(10) NOT NULL,
    trigger_indicator_value FLOAT NOT NULL,
    trigger_indicator_timeframe VARCHAR(10) NOT NULL,
    trigger_indicator_period INTEGER NOT NULL
);