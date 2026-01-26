import os
import threading
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Resolve the DB path from the project root to avoid CWD-dependent files.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_PATH = os.path.join(PROJECT_ROOT, "ticker.sqlite")
# engine = create_engine(f"sqlite:///{DB_PATH}?check_same_thread=False", pool_pre_ping=True)
engine = create_engine(f'postgresql+psycopg2://postgres:postgres@localhost:5432/forex')
Session = sessionmaker(bind=engine)
lock = threading.Lock()


@contextmanager
def session_scope():
    session = Session()
    try:
        lock.acquire()
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise
    finally:
        lock.release()
