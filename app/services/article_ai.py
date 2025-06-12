import os
import json
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload
from app.models.feed import Feed
from app.models.article import Article
from app.models.team import Team
from app.models.feed_per_team import feed_per_teams  # tabella many-to-many
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-3.5-turbo"

# ---------- Funzioni AI async ----------

async def generate_article_content(feeds: List[Feed]) -> dict:
    combined_text = "\n\n".join([f"Titolo: {f.title}\nTesto: {f.content}" for f in feeds])
    prompt = (
        "Sei un esperto giornalista sportivo.\n"
        "Genera un articolo che riorganizzi, senza sintetizzare, le notizie dei seguenti feed sul calciomercato.\n"
        "Scrivi un titolo accattivante e un testo articolato.\n"
        "Basati esclusivamente su quanto presente nei feed letti.\n"
        f"Feed:\n{combined_text}\n\n"
        "Rispondi in formato JSON con due campi: 'title' e 'content'."
    )
    try:
        response = await openai.ChatCompletion.acreate(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[generate_article_content] Errore OpenAI: {e}")
        return {"title": "Aggiornamenti Calciomercato", "content": "Errore nella generazione dell'articolo."}

async def update_article_content(old_content: str, new_feeds: List[Feed]) -> dict:
    combined_new_text = "\n\n".join([f"Titolo: {f.title}\nTesto: {f.content}" for f in new_feeds])
    prompt = (
        "Sei un esperto giornalista sportivo.\n"
        "Aggiorna questo articolo integrando le nuove informazioni ricevute con i nuovi feed.\n"
        "Aggiorna eventuali informazioni obsolete e aggiungi le nuove.\n"
        "senza cancellare informazioni utili già presenti.\n"
        f"Articolo precedente:\n{old_content}\n\n"
        f"Nuove notizie:\n{combined_new_text}\n\n"
        "Rispondi in formato JSON con 'title' e 'content' aggiornati."
    )
    try:
        response = await openai.ChatCompletion.acreate(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"[update_article_content] Errore OpenAI: {e}")
        return {"title": "Aggiornamenti Calciomercato", "content": old_content}

# ---------- Associazione feed-team ----------

async def associate_feeds_to_teams(db: AsyncSession):
    result = await db.execute(select(Feed).filter_by(processed=False))
    feeds = result.scalars().all()
    if not feeds:
        print("[associate_feeds_to_teams] Nessun feed da associare.")
        return

    result = await db.execute(select(Team))
    teams = result.scalars().all()

    to_insert = []
    for feed in feeds:
        text = f"{feed.title} {feed.content}".lower()
        for team in teams:
            if team.name.lower() in text:
                stmt_check = select(feed_per_teams).where(
                    (feed_per_teams.c.feed_id == feed.id) &
                    (feed_per_teams.c.team_id == team.id)
                )
                exists = await db.execute(stmt_check)
                if not exists.first():
                    to_insert.append({"feed_id": feed.id, "team_id": team.id})

    if to_insert:
        await db.execute(insert(feed_per_teams), to_insert)
        await db.commit()
        print(f"[associate_feeds_to_teams] Associazioni create: {len(to_insert)}")
    else:
        print("[associate_feeds_to_teams] Nessuna nuova associazione da creare.")

# ---------- Processo principale: lettura e scrittura articoli ----------

async def process_unprocessed_feeds(db: AsyncSession):
    result = await db.execute(
        select(Feed)
        .where(Feed.processed == False)
        .options(selectinload(Feed.teams))
        .order_by(Feed.published_at)
    )
    feeds = result.scalars().all()

    for feed in feeds:
        if not feed.teams:
            print(f"[{feed.id}] Nessun team associato. Feed ignorato.")
            continue

        if not feed.content:
            print(f"[{feed.id}] Feed senza contenuto. Ignorato.")
            continue

        team: Optional[Team] = feed.teams[0]
        if not team:
            print(f"[{feed.id}] Nessun team valido associato.")
            continue

        print(f"[{feed.id}] Associato al team: {team.name}, pubblicato: {feed.published_at}")

        article = team.article

        try:
            if article:
                print(f"[{feed.id}] → Aggiornamento articolo per team: {team.name}")
                updated = await update_article_content(article.content, [feed])
                article.title = updated["title"]
                article.content = updated["content"]
            else:
                print(f"[{feed.id}] → Generazione nuovo articolo per team: {team.name}")
                generated = await generate_article_content([feed])
                new_article = Article(
                    team_id=team.id,
                    title=generated["title"],
                    content=generated["content"],
                )
                db.add(new_article)
        except Exception as e:
            print(f"[{feed.id}] ❌ Errore durante la generazione/aggiornamento AI: {e}")
            continue  # passa al feed successivo

        try:
            feed.processed = True
            await db.commit()
            print(f"[{feed.id}] ✅ Feed processato correttamente.")
        except Exception as e:
            print(f"[{feed.id}] ❌ Errore durante il commit DB: {e}")
            await db.rollback()
