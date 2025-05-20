# src/dev_platform/infrastructure/database/session.py
from contextlib import contextmanager
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.config import DATABASE_URL  #   Assuming this holds the URL

Engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.config import DATABASE_URL  #   Assuming this holds the URL

Engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

@contextmanager
def db_session():
    """Context manager para sessões de banco de dados."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# #   src/dev_platform/infrastructure/database/session.py
# from contextlib import contextmanager
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from infrastructure.config import DATABASE_URL  #   Assuming this holds the URL

# Engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from infrastructure.config import DATABASE_URL  #   Assuming this holds the URL

# Engine = create_engine(DATABASE_URL)
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=Engine)

# def get_db_session():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()