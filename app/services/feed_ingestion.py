import feedparser
from sqlalchemy.orm import Session
from app.models.feed import Feed
import datetime

# Lista RSS da leggere (puoi metterla in config se vuoi)
RSS_FEEDS = [
    "https://www.gazzetta.it/rss/calciomercato.xml",
    "https://sport.sky.it/rss/calciomercato",
    # aggiungi altre fonti RSS
]

def ingest_feeds(db: Session):
    new_count = 0

    for rss_url in RSS_FEEDS:
        d = feedparser.parse(rss_url)
        feed_source = rss_url  # puoi mappare il nome reale se vuoi

        for entry in d.entries:
            # Usare link come feed_entry_id univoco (o guid se presente)
            feed_entry_id = getattr(entry, "id", None) or entry.link

            # Controlla duplicati
            existing = db.query(Feed).filter(Feed.feed_entry_id == feed_entry_id).first()
            if existing:
                continue

            # Parsing campi, adattati a seconda del feed
            title = entry.title if "title" in entry else ""
            link = entry.link if "link" in entry else ""
            summary = entry.summary if "summary" in entry else ""
            content = entry.get("content", [{"value": ""}])[0]["value"] if "content" in entry else summary

            # published_at parsing, fallback a ora corrente
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
