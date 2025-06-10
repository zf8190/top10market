# app/db/session.py

import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL non impostato nelle variabili ambiente")

# 🔁 Assicurati che l'URL inizi con "postgresql+asyncpg://" se usi PostgreSQL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# 🔌 Async engine
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)

# 🏭 Async session maker
async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

# 🧱 Base dichiarativa
Base = declarative_base()

# 🔁 Dipendenza asincrona per FastAPI
async def get_db():
    async with async_session() as session:
        yield session
