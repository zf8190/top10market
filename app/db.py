# app/db.py

import os
import ssl
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

# Carica variabili ambiente
load_dotenv()

# Recupera DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL non impostato nelle variabili ambiente")

# Converti in URL compatibile con asyncpg
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Configura SSL se necessario (es. Railway)
connect_args = {}
if "railway" in DATABASE_URL or "sslmode=require" in DATABASE_URL:
    ssl_context = ssl.create_default_context()
    connect_args = {"ssl": ssl_context}

# Crea engine asincrono
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

# Factory per sessioni asincrone
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# Base per i modelli
Base = declarative_base()

# Dipendenza per ottenere una sessione DB
async def get_db():
    async with async_session() as session:
        yield session

# Per chi ha bisogno direttamente dell'engine
def get_engine():
    return engine
