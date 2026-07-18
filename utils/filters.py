from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery

import database as db
from config import OWNER_ID


class IsAdmin(BaseFilter):
    """Foydalanuvchi admin (yoki owner) bo'lsa True qaytaradi."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id
        if user_id == OWNER_ID:
            return True
        return await db.is_admin(user_id)


class IsOwner(BaseFilter):
    """Faqat bosh admin (owner) uchun True qaytaradi."""

    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id
        if user_id == OWNER_ID:
            return True
        return await db.is_owner(user_id)