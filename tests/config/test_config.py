import src.config.db_config as db_config

def test_db_config_import():
    db_url = db_config.load_db_config()

    assert db_url is not None
    assert db_url.startswith("postgresql+psycopg2://")