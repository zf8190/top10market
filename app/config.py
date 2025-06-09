import os
from dotenv import load_dotenv

load_dotenv()  # Carica le variabili d'ambiente dal file .env

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
STATIC_URL = os.getenv("STATIC_URL", "/static/")  # Default fallback

# Opzionale: validazione semplice per assicurarsi che le variabili esistano
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment variables")

if not DATABASE_URL:
    raise ValueError("Missing DATABASE_URL in environment variables")
