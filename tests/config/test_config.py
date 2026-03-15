import src.config.db_config as db_config


def test_db_config_import():
    db_url = db_config.get_db_url()

    assert db_url is not None
