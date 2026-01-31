from prefect import task
from pydantic import SecretStr
from prefect_sqlalchemy import SqlAlchemyConnector, ConnectionComponents, SyncDriver

@task
def db_connection():
    connection_info = ConnectionComponents(
        driver=SyncDriver.POSTGRESQL_PSYCOPG2,
        username="postgres",
        password=SecretStr("postgres"),
        host="forex-db",
        port=5432,
        database="forex"
    )

    connector = SqlAlchemyConnector(connection_info=connection_info)
    connector.save("forex-connector")

if __name__ == "__main__":
    db_connection()