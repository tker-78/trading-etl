from sqlalchemy import create_engine, text
from src.config.db_config import get_db_url


def test_db_connection():
    engine = create_engine(get_db_url())
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
