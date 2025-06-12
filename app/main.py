from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import text
import os

from app.db import get_db, get_engine
from app.models.article import Article
from app.models.team import Team
from app.models import Base  # Assicura che importi Base con i modelli collegati
from app.config import STATIC_URL
from app.api.jobs import router as jobs_router

app = FastAPI()

# Inizializza le tabelle al primo avvio
@app.on_event("startup")
async def startup_event():
    db_url = os.getenv("DATABASE_URL", "❌ DATABASE_URL non trovato")
    print(f"🔧 Stringa di connessione al DB: {db_url}")

    try:
        async with get_engine().connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print("✅ Connessione al database riuscita! Risultato:", result.scalar())
    except Exception as e:
        print("❌ Errore nella connessione al database:", e)

    # Creazione delle tabelle
    try:
        async with get_engine().begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tabelle del database create (se non esistevano)")
    except Exception as e:
        print("❌ Errore nella creazione delle tabelle:", e)

# Includi le rotte API
app.include_router(jobs_router, prefix="/api")

# Static files (CSS, immagini, ecc.)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article).join(Team).order_by(Team.name)
    )
    articles = result.scalars().all()
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "articles": articles,
            "STATIC_URL": STATIC_URL
        }
    )

@app.get("/team/{team_name}", response_class=HTMLResponse)
async def read_article(team_name: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Article).join(Team).where(Team.name.ilike(team_name))
    )
    article = result.scalars().first()

    if not article:
        raise HTTPException(status_code=404, detail="Articolo non trovato")

    return templates.TemplateResponse(
        "article.html",
        {
            "request": request,
            "article": article,
            "STATIC_URL": STATIC_URL
        }
    )
