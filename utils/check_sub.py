from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

import database as db

NOT_MEMBER_STATUSES = ("left", "kicked")


async def is_user_subscribed_to_channel(bot: Bot, user_id: int, chat_id: str) -> bool:
    """Faqat PUBLIC telegram turidagi kanallar uchun getChatMember orqali tekshiradi.
    Bu funksiya o'zgarmadi - eski public kanal logikasi bir xil ishlashda davom etadi."""
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status not in NOT_MEMBER_STATUSES
    except TelegramBadRequest:
        # Bot kanalda admin emas yoki chat_id noto'g'ri - xavfsizlik uchun False qaytaramiz
        return False
    except Exception:
        return False


async def get_unsubscribed_channels(bot: Bot, user_id: int, channels) -> list:
    """
    channels - database.get_channels() natijasi.

    - type == 'telegram' (PUBLIC kanal): eski usulda getChatMember orqali tekshiriladi.
    - type == 'telegram_private' (Join Request kanal): getChatMember ISHLATILMAYDI,
      chunki so'rov yuborgan foydalanuvchi hali "a'zo" hisoblanmaydi. Buning o'rniga
      join_requests jadvalidan foydalanuvchi shu kanalga so'rov yuborganmi tekshiriladi.
    - Instagram/YouTube/TikTok/Website turlari har doim 'obuna bo'lgan' deb hisoblanadi,
      chunki ularni Telegram API orqali tekshirib bo'lmaydi - faqat link ochiladi.
    """
    unsubscribed = []
    for channel in channels:
        if channel["type"] == "telegram" and channel["chat_id"]:
            subscribed = await is_user_subscribed_to_channel(bot, user_id, channel["chat_id"])
            if not subscribed:
                unsubscribed.append(channel)
        elif channel["type"] == "telegram_private":
            has_request = await db.has_active_join_request(user_id, channel["id"])
            if not has_request:
                unsubscribed.append(channel)
    return unsubscribed