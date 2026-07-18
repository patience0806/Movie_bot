from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

import database as db


class BanCheckMiddleware(BaseMiddleware):
    """Ban qilingan foydalanuvchilarning xabarlarini/callbacklarini bloklaydi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            record = await db.get_user(user.id)
            if record and record["is_banned"] == 1:
                if isinstance(event, Message):
                    await event.answer("🚫 Siz botdan foydalanishdan bloklangansiz.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 Siz botdan foydalanishdan bloklangansiz.", show_alert=True)
                return
        return await handler(event, data)


class ActivityMiddleware(BaseMiddleware):
    """Har bir harakatda ro'yxatdan o'tgan foydalanuvchining last_active vaqtini yangilaydi."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is not None:
            record = await db.get_user(user.id)
            if record:
                await db.update_last_active(user.id)
        return await handler(event, data)