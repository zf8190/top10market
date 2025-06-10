import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL non impostato nelle variabili ambiente")

# Se l'URL inizia con postgresql://, trasformalo in postgresql+asyncpg://
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Attiva SSL solo se siamo in staging/prod (es. presenza 'railway' nell'URL)
connect_args = {}
if "railway" in DATABASE_URL:
    connect_args = {"sslmode": "require"}

# Crea async engine con o senza SSL
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

async_session = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db():
    async with async_session() as session:
        yield session

def get_engine():
    return engine
