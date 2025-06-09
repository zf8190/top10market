from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from sqlalchemy.orm import Session

from app.db import get_db
from app.models.article import Article
from app.models.team import Team
from app.config import STATIC_URL
from app.api.jobs import router as jobs_router

app = FastAPI()

app.include_router(jobs_router, prefix="/api")


# Monta la cartella static per CSS, immagini, ecc.
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configura i template Jinja2
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def read_home(request: Request, db: Session = Depends(get_db)):
    articles = (
        db.query(Article)
        .join(Team)
        .order_by(Team.name)
        .all()
    )
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "articles": articles,
            "STATIC_URL": STATIC_URL
        }
    )

@app.get("/team/{team_name}", response_class=HTMLResponse)
def read_article(team_name: str, request: Request, db: Session = Depends(get_db)):
    article = (
        db.query(Article)
        .join(Team)
        .filter(Team.name.ilike(team_name))
        .first()
    )
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
