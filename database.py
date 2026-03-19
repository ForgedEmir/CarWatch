from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Create data directory if it doesn't exist (for sqlite fallback)
os.makedirs("data", exist_ok=True)

# Default to SQLite if POSTGRES_URL isn't set
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/carwatch.db")

engine = create_engine(
    DATABASE_URL, 
    # Only need check_same_thread for SQLite
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
