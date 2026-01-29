CREATE DATABASE forex;

DROP TABLE ticker_usd_jpy;

CREATE TABLE IF NOT EXISTS ticker_usd_jpy (
    time TIMESTAMP PRIMARY KEY,
    bid FLOAT,
    ask FLOAT
);