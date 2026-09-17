import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import database as db
from config import BOT_TOKEN, OWNER_ID
from utils.middlewares import BanCheckMiddleware, ActivityMiddleware

from handlers.user import start as user_start
from handlers.user import subscribe as user_subscribe
from handlers.user import search as user_search
from handlers.user import callbacks as user_callbacks
from handlers.user import premium as user_premium

from handlers.admin import panel as admin_panel
from handlers.admin import movies as admin_movies
from handlers.admin import channels as admin_channels
from handlers.admin import ads as admin_ads
from handlers.admin import premium as admin_premium
from handlers.admin import admins as admin_admins

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    await db.init_db()

    if OWNER_ID:
        await db.add_admin(telegram_id=OWNER_ID, added_by=OWNER_ID, is_owner=True)

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.middleware(BanCheckMiddleware())
    dp.callback_query.middleware(BanCheckMiddleware())
    dp.message.middleware(ActivityMiddleware())
    dp.callback_query.middleware(ActivityMiddleware())

    # Admin routerlar (IsAdmin filtri o'z ichida qo'llangan) - user routerlardan OLDIN turishi shart,
    # aks holda admin FSM holatlaridagi matnlar ham "kino kod qidiruvi" catch-all handleriga tushib qoladi
    dp.include_router(admin_panel.router)
    dp.include_router(admin_movies.router)
    dp.include_router(admin_channels.router)
    dp.include_router(admin_ads.router)
    dp.include_router(admin_premium.router)
    dp.include_router(admin_admins.router)

    # User routerlar
    dp.include_router(user_start.router)
    dp.include_router(user_subscribe.router)
    dp.include_router(user_premium.router)
    dp.include_router(user_search.router)
    dp.include_router(user_callbacks.router)

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot ishga tushdi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot to'xtatildi.")