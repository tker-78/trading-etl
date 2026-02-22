ALTER TABLE dim_currency
ADD COLUMN currency_pair_key TEXT DEFAULT '' NOT NULL;

ALTER TABLE dim_currency
DROP COLUMN currency_pair_key;