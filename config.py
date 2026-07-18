import os
from dotenv import load_dotenv

load_dotenv()

# Bot token - @BotFather dan oling
BOT_TOKEN = os.getenv("8952038907:AAHhdzXaCGKzp4fbrkyL0-hJrcwKq_0b3-I", "8952038907:AAHhdzXaCGKzp4fbrkyL0-hJrcwKq_0b3-I")

# Bosh admin (owner) Telegram ID raqami - butun son bo'lishi shart
OWNER_ID = int(os.getenv("2140190947", "2140190947"))

# Database fayl yo'li
DB_PATH = os.getenv("DB_PATH", "movies.db")

# Har bir sahifada nechta kino ko'rsatilishi
MOVIES_PER_PAGE = 10

# /start bosilganda ko'rsatiladigan xabar
START_TEXT = (
    "🎬 Assalomu alaykum, {name}!\n\n"
    "Kerakli kinoning kodini yuboring."
)