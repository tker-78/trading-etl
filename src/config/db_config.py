import os
from configparser import ConfigParser

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

def load_db_config():
    config = ConfigParser()
    ini_path = os.path.join(PROJECT_ROOT, 'config', 'config.ini')
    config.read(ini_path)
    username = config.get('db', 'username')
    host = config.get('db', 'host')
    port = config.get('db', 'port')
    db_name = config.get('db', 'db_name')
    password = config.get('db', 'password')


    db_url = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{db_name}"
    return db_url
