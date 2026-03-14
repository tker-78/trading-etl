"""baseline_current_schema

Revision ID: e2444ebd2a06
Revises:
Create Date: 2026-03-09 06:47:56.219360

"""

from typing import Sequence, Union
from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e2444ebd2a06"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = PROJECT_ROOT / "src" / "database" / "sql"


def _read_sql(filename: str) -> str:
    return (SQL_DIR / filename).read_text(encoding="utf-8")


def upgrade() -> None:
    # 1) schema

    op.execute("CREATE SCHEMA IF NOT EXISTS ohlc")
    op.execute("CREATE SCHEMA IF NOT EXISTS ticker")

    # 2) create

    # op.execute(_read_sql("create_dimensions.sql"))

    op.execute("""
    CREATE TABLE dim_currency (
    id SERIAL PRIMARY KEY,
    base_currency CHAR(3) NOT NULL,
    quote_currency CHAR(3) NOT NULL,
    currency_pair_code TEXT NOT NULL, -- e.g. 'USD/JPY'
    currency_pair_symbol TEXT NOT NULL, -- e.g. 'USDJPY'
    UNIQUE (base_currency, quote_currency),
    UNIQUE (currency_pair_code),
    UNIQUE (currency_pair_symbol)
    );
    """)

    op.execute("""
    CREATE TABLE dim_timeframe (
    id SERIAL PRIMARY KEY,
    timeframe_code TEXT NOT NULL, -- e.g. '1m', '5m', '30m'
    timeframe_name TEXT NOT NULL, -- e.g. '1 minute', '5 minutes', '30 minutes'
    duration_seconds INTEGER NOT NULL,  -- e.g. 60, 300, 1800
    UNIQUE (timeframe_code),
    UNIQUE (duration_seconds)
);
    """)

    # op.execute(_read_sql("create_fact_buysell_events.sql"))
    op.execute("""
    CREATE TABLE fact_buysell_events (
    event_id SERIAL,
    event_datetime TIMESTAMP NOT NULL,
    currency_id INTEGER NOT NULL,
    price FLOAT NOT NULL,
    quantity INTEGER NOT NULL,
    event_type VARCHAR(10) NOT NULL, -- e.g. buy or sell
    trigger_indicator_name VARCHAR(10) NOT NULL,
    trigger_indicator_value FLOAT NOT NULL,
    trigger_indicator_timeframe VARCHAR(10) NOT NULL,
    trigger_indicator_period INTEGER NOT NULL,
    PRIMARY KEY (event_datetime, currency_id, event_type, trigger_indicator_name)
    );
    """)

    # op.execute(_read_sql("create_fact_ema.sql"))
    op.execute("""
    CREATE TABLE fact_ema (
    time TIMESTAMP NOT NULL,
    currency_id INTEGER NOT NULL REFERENCES dim_currency(id),
    timeframe_id INTEGER NOT NULL,
    period INTEGER NOT NULL,
    calc_version TEXT NOT NULL,
    value FLOAT,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (time, currency_id, timeframe_id, period, calc_version)
    );
    """)

    # op.execute(_read_sql("create_fact_rsi.sql"))
    op.execute("""
    CREATE TABLE fact_rsi (
    time TIMESTAMP NOT NULL,
    currency_id INTEGER NOT NULL REFERENCES dim_currency(id),
    timeframe_id INTEGER NOT NULL,
    period INTEGER NOT NULL,
    calc_version TEXT NOT NULL,
    value FLOAT,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (time, currency_id, timeframe_id, period, calc_version)
    );
    """)

    # op.execute(_read_sql("create_fact_sma.sql"))
    op.execute("""
    CREATE TABLE fact_sma (
    time TIMESTAMP NOT NULL,
    currency_id INTEGER NOT NULL REFERENCES dim_currency(id),
    timeframe_id INTEGER NOT NULL,
    period INTEGER NOT NULL,
    calc_version TEXT NOT NULL,
    value FLOAT,
    calculated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (time, currency_id, timeframe_id, period, calc_version)
    );
    """)

    # 3) Insert

    # op.execute(_read_sql("insert_dimensions.sql"))
    op.execute("""
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
       ('4h', '4hour', 14400)
ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop in dependency order (children -> parents) to avoid FK violations.
    op.drop_table("fact_ema")
    op.drop_table("fact_rsi")
    op.drop_table("fact_sma")
    op.drop_table("fact_buysell_events")
    op.drop_table("dim_timeframe")
    op.drop_table("dim_currency")
