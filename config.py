import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

if not BOT_TOKEN:
    raise SystemExit("BOT_TOKEN is not set. Create a .env file (see .env.example) and set BOT_TOKEN.")
