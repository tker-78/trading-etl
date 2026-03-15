import os
from configparser import ConfigParser
from sqlalchemy.engine import URL

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)


def get_db_url():
    config = ConfigParser()
    ini_path = os.path.join(PROJECT_ROOT, "config", "config.ini")

    if not os.path.exists(ini_path):
        raise FileNotFoundError(f"config.ini not found in {PROJECT_ROOT}")

    config.read(ini_path)
    username = config.get("db", "username")
    host = config.get("db", "host")
    port = config.get("db", "port")
    db_name = config.get("db", "db_name")
    password = config.get("db", "password")

    return URL.create(
        drivername="postgresql+psycopg2",
        username=username,
        host=host,
        port=int(port),
        database=db_name,
        password=str(password),
    )
