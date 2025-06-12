import os
import json
import datetime
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from app.models.feed import Feed
from app.models.article import Article
from app.models.team import Team
from app.models.feed_per_team import feed_per_teams  # la tabella many-to-many

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-3.5-turbo"

# ---------- Funzioni AI ----------

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


# ---------- Funzione di associazione feed-team ----------

async def associate_feeds_to_teams(db: AsyncSession):
    """
    Associa i feed non processati ai team basandosi sul matching del nome del team nel titolo o contenuto del feed.
    Inserisce i record nella tabella feed_per_teams se non esistono già.
    """
    # Prendi tutti i feed non processati
    result = await db.execute(select(Feed).filter(Feed.processed == False))
    feeds = result.scalars().all()

    if not feeds:
        print("[associate_feeds_to_teams] Nessun feed non processato da associare.")
        return

    # Prendi tutti i team
    result = await db.execute(select(Team))
    teams = result.scalars().all()

    # Mappa feed_id -> set(team_id)
    feed_team_map = {}

    for feed in feeds:
        feed_text = f"{feed.title} {feed.content}".lower()
        associated_team_ids = set()

        for team in teams:
            team_name_lower = team.name.lower()
            if team_name_lower in feed_text:
                associated_team_ids.add(team.id)

        feed_team_map[feed.id] = associated_team_ids

    # Inserisci le associazioni in feed_per_teams se non già esistenti
    for feed_id, team_ids in feed_team_map.items():
        for team_id in team_ids:
            # Verifica se esiste già associazione
            stmt_check = select(feed_per_teams).where(
                (feed_per_teams.c.feed_id == feed_id) &
                (feed_per_teams.c.team_id == team_id)
            )
            result = await db.execute(stmt_check)
            exists = result.first()
            if not exists:
                stmt_insert = insert(feed_per_teams).values(feed_id=feed_id, team_id=team_id)
                await db.execute(stmt_insert)

    await db.commit()
    print(f"[associate_feeds_to_teams] Associazioni create per {len(feeds)} feed.")


# ---------- Funzioni principali ----------

async def generate_daily_articles(db: AsyncSession):
    now = datetime.datetime.now()

    # Prima associa le feeds ai team
    await associate_feeds_to_teams(db)

    result = await db.execute(select(Feed).filter(Feed.processed == False))
    new_feeds = result.scalars().all()
    if not new_feeds:
        print("[generate_daily_articles] Nessun feed nuovo da processare.")
        return

    feed_map = {f.id: f for f in new_feeds}

    stmt = select(feed_per_teams.c.team_id, feed_per_teams.c.feed_id).where(
        feed_per_teams.c.feed_id.in_(feed_map.keys())
    )
    result = await db.execute(stmt)
    associations = result.fetchall()

    feeds_by_team = {}
    for team_id, feed_id in associations:
        feeds_by_team.setdefault(team_id, []).append(feed_map[feed_id])

    for team_id, feeds_list in feeds_by_team.items():
        print(f"[generate_daily_articles] Genero articolo per team_id={team_id} con {len(feeds_list)} feed.")
        article_data = generate_article_content(feeds_list)

        result = await db.execute(select(Article).filter(Article.team_id == team_id))
        article = result.scalars().first()

        if article:
            article.title = article_data.get("title", article.title)
            article.content = article_data.get("content", article.content)
            article.summary = article.content[:200]
            article.last_updated = now
            article.sources = ", ".join(set(f.feed_source for f in feeds_list))
        else:
            article = Article(
                team_id=team_id,
                title=article_data.get("title", ""),
                content=article_data.get("content", ""),
                summary=article_data.get("content", "")[:200],
                last_updated=now,
                sources=", ".join(set(f.feed_source for f in feeds_list))
            )
            db.add(article)

        for f in feeds_list:
            f.processed = True

    await db.commit()
    print("[generate_daily_articles] Completato.")


async def update_hourly_articles(db: AsyncSession):
    now = datetime.datetime.now()

    # Prima associa le feeds ai team
    await associate_feeds_to_teams(db)

    result = await db.execute(select(Feed).filter(Feed.processed == False))
    new_feeds = result.scalars().all()
    if not new_feeds:
        print("[update_hourly_articles] Nessun feed nuovo da processare.")
        return

    feed_map = {f.id: f for f in new_feeds}

    stmt = select(feed_per_teams.c.team_id, feed_per_teams.c.feed_id).where(
        feed_per_teams.c.feed_id.in_(feed_map.keys())
    )
    result = await db.execute(stmt)
    associations = result.fetchall()

    feeds_by_team = {}
    for team_id, feed_id in associations:
        feeds_by_team.setdefault(team_id, []).append(feed_map[feed_id])

    for team_id, feeds_list in feeds_by_team.items():
        print(f"[update_hourly_articles] Aggiorno articolo per team_id={team_id} con {len(feeds_list)} feed.")
        result = await db.execute(select(Article).filter(Article.team_id == team_id))
        article = result.scalars().first()

        if article:
            article_data = update_article_content(article.content, feeds_list)
            article.title = article_data.get("title", article.title)
            article.content = article_data.get("content", article.content)
            article.summary = article.content[:200]
            article.last_updated = now
            existing_sources = set(article.sources.split(", ")) if article.sources else set()
            new_sources = set(f.feed_source for f in feeds_list)
            article.sources = ", ".join(existing_sources.union(new_sources))
        else:
            article_data = generate_article_content(feeds_list)
            article = Article(
                team_id=team_id,
                title=article_data.get("title", ""),
                content=article_data.get("content", ""),
                summary=article_data.get("content", "")[:200],
                last_updated=now,
                sources=", ".join(set(f.feed_source for f in feeds_list))
            )
            db.add(article)

        for f in feeds_list:
            f.processed = True

    await db.commit()
    print("[update_hourly_articles] Completato.")
