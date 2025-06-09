import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # Es: postgresql://user:pass@host:port/dbname

if not DATABASE_URL:
    raise ValueError("DATABASE_URL non impostato nelle variabili ambiente")

# Creiamo il motore di connessione
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Factory per sessioni DB
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base declarativa, importata poi in models/__init__.py
from sqlalchemy.orm import declarative_base
Base = declarative_base()

def get_engine():
    return engine

def get_db():
    """
    Dependency da usare in FastAPI o similari per ottenere una sessione DB.
    In Flask si può gestire diversamente.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
