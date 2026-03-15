import os
import src.config.db_config as db_config


def test_db_config_import():
    env = os.getenv('APP_ENV')
    assert env == 'test'
    db_url = db_config.get_db_url()
    assert db_url.database == 'forex-test'

