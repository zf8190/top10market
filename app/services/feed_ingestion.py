import feedparser
from sqlalchemy.orm import Session
from app.models.feed import Feed
from app.config import load_rss_feeds
import datetime

def ingest_feeds(db: Session):
    rss_urls = load_rss_feeds()
    new_count = 0

    for rss_url in rss_urls:
        d = feedparser.parse(rss_url)
        feed_source = rss_url  # puoi usare un mapping se vuoi un nome più leggibile

        for entry in d.entries:
            # ID univoco del feed
            feed_entry_id = getattr(entry, "id", None) or entry.link

            # Evita duplicati
            if db.query(Feed).filter(Feed.feed_entry_id == feed_entry_id).first():
                continue

            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            summary = getattr(entry, "summary", "")
            content = entry.get("content", [{"value": ""}])[0]["value"] if "content" in entry else summary

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

    db.commit()
    print(f"[FeedIngestion] Inseriti {new_count} nuovi feed.")
