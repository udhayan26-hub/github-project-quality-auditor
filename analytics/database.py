import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from analytics.models import Base

load_dotenv()

# Read Database URL from environment, fallback to local SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///analytics.db")

# SQLite needs different parameters compared to PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    # check_same_thread=False is crucial for multi-threaded Streamlit apps
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL standard pool configuration
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=20)

# Session factory
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
db_session = scoped_session(session_factory)

def init_db():
    """Initializes the database, creating all tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

@contextmanager
def get_db():
    """Context manager for database sessions. Handles clean closing."""
    session = db_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        db_session.remove()
