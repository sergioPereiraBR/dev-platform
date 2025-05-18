#   src/infrastructure/database/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.infrastructure.config import DATABASE_URL  #   Assuming this holds the URL

Engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()