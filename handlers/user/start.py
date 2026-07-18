from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message

import database as db
from handlers.user.subscribe import get_pending_channels, send_subscription_prompt, send_main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    await db.add_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username or "",
        full_name=message.from_user.full_name or ""
    )

    pending = await get_pending_channels(bot, message.from_user.id)
    if pending:
        await send_subscription_prompt(message, bot)
        return

    await send_main_menu(message, message.from_user.id)