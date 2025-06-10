import os
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.feed import Feed
from app.models.article import Article
import openai
import json
import datetime

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-3.5-turbo"

def generate_article_content(feeds: List[Feed]) -> dict:
    combined_text = "\n\n".join([f"Titolo: {f.title}\nTesto: {f.content}" for f in feeds])
    prompt = (
        "Sei un esperto giornalista sportivo.\n"
        "Genera un articolo che sintetizzi le notizie dei seguenti feed sul calciomercato.\n"
        "Scrivi un titolo accattivante e un testo articolato.\n"
        "Non aggiungere informazioni non presenti.\n"
        f"Feed:\n{combined_text}\n\n"
        "Rispondi in formato JSON con due campi: 'title' e 'content'."
    )

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"title": "Aggiornamenti Calciomercato", "content": response.choices[0].message.content}

def update_article_content(old_content: str, new_feeds: List[Feed]) -> dict:
    combined_new_text = "\n\n".join([f"Titolo: {f.title}\nTesto: {f.content}" for f in new_feeds])
    prompt = (
        "Sei un esperto giornalista sportivo.\n"
        "Aggiorna questo articolo con le nuove notizie qui sotto.\n"
        "Mantieni tutte le info importanti precedenti, aggiorna se serve, aggiungi nuove notizie.\n"
        "Non cancellare informazioni utili già presenti.\n"
        f"Articolo precedente:\n{old_content}\n\n"
        f"Nuove notizie:\n{combined_new_text}\n\n"
        "Rispondi in formato JSON con 'title' e 'content' aggiornati."
    )

    response = openai.ChatCompletion.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=1000
    )
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        return {"title": "Aggiornamenti Calciomercato", "content": response.choices[0].message.content}


# --- QUI FUNZIONI ASINCRONE CON DB ---

async def generate_daily_articles(db: AsyncSession):
    """
    Funzione da chiamare alle 8:00 AM.
    Legge tutti i feed del giorno (o non processati),
    genera 10 articoli (uno per ogni team con feed),
    e li salva nel DB (creando o sovrascrivendo).
    Marca tutti i feed come processati.
    """
    now = datetime.datetime.now()

    result = await db.execute(select(Feed).filter(Feed.processed == False))
    new_feeds = result.scalars().all()
    if not new_feeds:
        print("Nessun feed nuovo da processare per la generazione giornaliera.")
        return

    # Raggruppa per team
    feeds_by_team = {}
    for f in new_feeds:
        feeds_by_team.setdefault(f.team_id, []).append(f)

    for team_id, feeds_list in feeds_by_team.items():
        article_data = generate_article_content(feeds_list)

        result = await db.execute(select(Article).filter(Article.team_id == team_id))
        article = result.scalars().first()

        if article:
            article.title = article_data.get("title", article.title)
            article.content = article_data.get("content", article.content)
            article.summary = article.content[:200]
            article.last_updated = now
            article.sources = ", ".join(set([f.feed_source for f in feeds_list]))
        else:
            article = Article(
                team_id=team_id,
                title=article_data.get("title", ""),
                content=article_data.get("content", ""),
                summary=article_data.get("content", "")[:200],
                last_updated=now,
                sources=", ".join(set([f.feed_source for f in feeds_list]))
            )
            db.add(article)

        # Marca feed come processati
        for f in feeds_list:
            f.processed = True

    await db.commit()

async def update_hourly_articles(db: AsyncSession):
    """
    Funzione da chiamare ogni ora dalle 9 in poi.
    Legge solo i nuovi feed non processati,
    aggiorna i relativi articoli integrando o modificando contenuti,
    marca i feed come processati.
    """
    now = datetime.datetime.now()

    result = await db.execute(select(Feed).filter(Feed.processed == False))
    new_feeds = result.scalars().all()
    if not new_feeds:
        print("Nessun feed nuovo da processare per aggiornamento orario.")
        return

    feeds_by_team = {}
    for f in new_feeds:
        feeds_by_team.setdefault(f.team_id, []).append(f)

    for team_id, feeds_list in feeds_by_team.items():
        result = await db.execute(select(Article).filter(Article.team_id == team_id))
        article = result.scalars().first()

        if article:
            article_data = update_article_content(article.content, feeds_list)
            article.title = article_data.get("title", article.title)
            article.content = article_data.get("content", article.content)
            article.summary = article.content[:200]
            article.last_updated = now
            existing_sources = set(article.sources.split(", ")) if article.sources else set()
            new_sources = set([f.feed_source for f in feeds_list])
            article.sources = ", ".join(existing_sources.union(new_sources))
        else:
            article_data = generate_article_content(feeds_list)
            article = Article(
                team_id=team_id,
                title=article_data.get("title", ""),
                content=article_data.get("content", ""),
                summary=article_data.get("content", "")[:200],
                last_updated=now,
                sources=", ".join(set([f.feed_source for f in feeds_list]))
            )
            db.add(article)

        for f in feeds_list:
            f.processed = True

    await db.commit()
