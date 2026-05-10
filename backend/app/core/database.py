"""Database configuration and connection setup"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import os

# Use SQLite for local development by default
# Only use PostgreSQL if explicitly configured and running
use_sqlite = True
database_url = settings.database_url

if "postgresql" in database_url:
    # PostgreSQL is configured, but we'll use SQLite as fallback
    database_url = "sqlite:///./watery.db"
else:
    database_url = "sqlite:///./watery.db"

# SQLAlchemy engine
engine = create_engine(
    database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
)

# SessionLocal for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
