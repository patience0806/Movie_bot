from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

NOT_MEMBER_STATUSES = ("left", "kicked")


async def is_user_subscribed_to_channel(bot: Bot, user_id: int, chat_id: str) -> bool:
    """Faqat telegram turidagi kanallar uchun getChatMember orqali tekshiradi."""
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status not in NOT_MEMBER_STATUSES
    except TelegramBadRequest:
        return False
    except Exception:
        return False


async def get_unsubscribed_channels(bot: Bot, user_id: int, channels) -> list:
    """
    Faqat type == 'telegram' bo'lgan kanallar tekshiriladi.
    Instagram/YouTube/TikTok/Website turlari har doim 'obuna bo'lgan' deb hisoblanadi,
    chunki ularni Telegram API orqali tekshirib bo'lmaydi - faqat link ochiladi.
    """
    unsubscribed = []
    for channel in channels:
        if channel["type"] == "telegram" and channel["chat_id"]:
            subscribed = await is_user_subscribed_to_channel(bot, user_id, channel["chat_id"])
            if not subscribed:
                unsubscribed.append(channel)
    return unsubscribed