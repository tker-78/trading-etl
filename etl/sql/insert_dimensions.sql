INSERT INTO dim_currency (base_currency, quote_currency, currency_pair_code, currency_pair_symbol)
VALUES ('USD', 'JPY', 'USD/JPY', 'USD_JPY'),
       ('EUR', 'JPY', 'EUR/JPY', 'EUR_JPY'),
       ('GBP', 'JPY', 'GBP/JPY', 'GBP_JPY'),
       ('AUD', 'JPY', 'AUD/JPY', 'AUD_JPY'),
       ('CAD', 'JPY', 'CAD/JPY', 'CAD_JPY'),
       ('CHF', 'JPY', 'CHF/JPY', 'CHF_JPY')
ON CONFLICT DO NOTHING;

INSERT INTO dim_timeframe (timeframe_code, timeframe_name, duration_seconds)
VALUES ('1m', '1min', 60),
       ('5m', '5min', 300),
       ('30m', '30min', 1800),
       ('1h', '1hour', 3600),
       ('4h', '4hour', 14400);
