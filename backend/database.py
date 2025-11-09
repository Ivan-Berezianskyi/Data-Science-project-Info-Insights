from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

# Create database engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Connection pool size
    max_overflow=20,  # Additional connections beyond pool_size
    echo=False  # Set to True for SQL query logging
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# Dependency to get database session
def get_db():
    """
    Dependency function to provide database session.
    Use this in FastAPI route dependencies.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database by creating all tables.
    Run this once to set up the database schema.
    
    IMPORTANT: This function only creates tables if they don't exist.
    It does NOT modify existing tables or add new columns to existing tables.
    For schema changes (like adding columns), use Alembic migrations or manual SQL.
    """
    from models import Chat, Message
    Base.metadata.create_all(bind=engine)

