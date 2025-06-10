import os
from dotenv import load_dotenv
import json

# Percorso del file feeds.json
FEED_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "feeds.json")

# Carica le variabili d’ambiente PRIMA di usarle
load_dotenv()

# Ora puoi accedere in sicurezza alle env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
STATIC_URL = os.getenv("STATIC_URL", "/static/")  # Default fallback

# Correggi DATABASE_URL per asyncpg e sslmode (Railway richiede ssl)
if DATABASE_URL:
    if DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "?" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
    elif "sslmode" not in DATABASE_URL:
        DATABASE_URL += "&sslmode=require"

# Carica gli RSS dal file esterno
def load_rss_feeds():
    with open(FEED_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# RSS_FEEDS disponibile da qui
RSS_FEEDS = load_rss_feeds()

# Validazioni semplici
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment variables")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in environment variables")
