CREATE DATABASE forex;

CREATE SCHEMA IF NOT EXISTS usd_jpy;

DROP TABLE ticker_usd_jpy;

CREATE TABLE IF NOT EXISTS ticker_usd_jpy (
    time TIMESTAMP PRIMARY KEY,
    bid FLOAT,
    ask FLOAT
);