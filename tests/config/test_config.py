import os
import src.config.db_config as db_config


def test_db_config_import():
    env = os.getenv('APP_ENV')
    db_url = db_config.get_db_url()
    if env == 'dev':
        assert db_url.database == 'forex'
    elif env == 'test':
        assert db_url.database == 'forex-test'
    else:
        assert db_url.database == 'forex'

