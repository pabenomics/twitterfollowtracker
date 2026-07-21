import os

# Il faut récupérer les secrets que tu as mis dans l'onglet Settings de GitHub
API_KEY = os.getenv("API_KEY")
API_HOST = "twitter241.p.rapidapi.com" # <--- VÉRIFIE QUE C'EST BIEN TON HOST RAPIDAPI
BASE_URL = f"https://{API_HOST}"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Récupération des cibles
TARGETS_RAW = os.getenv("TARGETS", "")
TARGETS = [t.strip() for t in TARGETS_RAW.split(",") if t.strip()]