import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.models import Base

# Ensure SQLite data folder exists if using local SQLite path
if settings.DATABASE_URL.startswith("sqlite"):
    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

# Create engine
# check_same_thread=False is required for SQLite when used across threads/tasks
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """Creates all database tables defined in models.py."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Session:
    """Context-safe helper to yield a session and ensure clean closure."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
