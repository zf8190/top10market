# app/services/feed_ingestion.py

import feedparser
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.feed import Feed
from app.config import load_rss_feeds
import datetime

MAX_LEN = 255

def truncate_string(s: str, max_len: int = MAX_LEN) -> str:
    if s is None:
        return ""
    return s[:max_len]

async def ingest_feeds(db: AsyncSession):
    rss_urls = load_rss_feeds()
    new_count = 0

    for rss_url in rss_urls:
        d = feedparser.parse(rss_url)
        feed_source = truncate_string(rss_url)

        for entry in d.entries:
            feed_entry_id = truncate_string(getattr(entry, "id", None) or getattr(entry, "link", ""))

            # Evita duplicati
            result = await db.execute(select(Feed).where(Feed.feed_entry_id == feed_entry_id))
            existing = result.scalars().first()
            if existing:
                continue

            title = truncate_string(getattr(entry, "title", ""))
            link = truncate_string(getattr(entry, "link", ""))
            summary = truncate_string(getattr(entry, "summary", ""))
            content = entry.get("content", [{"value": ""}])[0]["value"]  # lascio content senza troncamento

            try:
                published_at = datetime.datetime(*entry.published_parsed[:6])
            except Exception:
                published_at = datetime.datetime.utcnow()

            new_feed = Feed(
                feed_source=feed_source,
                feed_entry_id=feed_entry_id,
                title=title,
                link=link,
                summary=summary,
                content=content,
                published_at=published_at,
                processed=False
            )

            db.add(new_feed)
            new_count += 1

    await db.commit()
    print(f"[FeedIngestion] Inseriti {new_count} nuovi feed.")
