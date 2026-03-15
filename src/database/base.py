import threading
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from src.config.db_config import get_db_url

Base = declarative_base()
engine = create_engine(get_db_url())
Session = sessionmaker(bind=engine)
lock = threading.Lock()


@contextmanager
def session_scope():
    session = Session()
    try:
        lock.acquire()
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        lock.release()
        session.close()
