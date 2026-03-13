"""baseline_current_schema

Revision ID: e2444ebd2a06
Revises: 
Create Date: 2026-03-09 06:47:56.219360

"""
from typing import Sequence, Union
from pathlib import Path

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e2444ebd2a06'
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

    op.execute(_read_sql("create_dimensions.sql"))

    op.execute(_read_sql("create_fact_buysell_events.sql"))

    op.execute(_read_sql("create_fact_ema.sql"))

    op.execute(_read_sql("create_fact_rsi.sql"))

    op.execute(_read_sql("create_fact_sma.sql"))

    # 3) Insert

    op.execute(_read_sql("insert_dimensions.sql"))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop in dependency order (children -> parents) to avoid FK violations.
    op.drop_table("fact_ema")
    op.drop_table("fact_rsi")
    op.drop_table("fact_sma")
    op.drop_table("fact_buysell_events")
    op.drop_table("dim_timeframe")
    op.drop_table("dim_currency")
