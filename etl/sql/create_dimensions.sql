CREATE TABLE IF NOT EXISTS dim_currency (
    id SERIAL PRIMARY KEY,
    base_currency CHAR(3) NOT NULL,
    quote_currency CHAR(3) NOT NULL,
    currency_pair_code TEXT NOT NULL, -- e.g. 'USD/JPY'
    currency_pair_symbol TEXT NOT NULL, -- e.g. 'USDJPY'

    UNIQUE (base_currency, quote_currency),
    UNIQUE (currency_pair_code),
    UNIQUE (currency_pair_symbol)
);

CREATE TABLE IF NOT EXISTS dim_timeframe (
    id SERIAL PRIMARY KEY,
    timeframe_code TEXT NOT NULL, -- e.g. '1m', '5m', '30m'
    timeframe_name TEXT NOT NULL, -- e.g. '1 minute', '5 minutes', '30 minutes'
    duration_seconds INTEGER NOT NULL,  -- e.g. 60, 300, 1800
    UNIQUE (timeframe_code),
    UNIQUE (duration_seconds)
);