import logging

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter

import database as db

logger = logging.getLogger(__name__)

# Telegram getChatMember qaytarishi mumkin bo'lgan barcha statuslar orasidan
# faqat shular "a'zo" hisoblanadi (so'ralgan aniq ro'yxat bo'yicha)
MEMBER_STATUSES = ("member", "administrator", "creator")


async def is_user_subscribed_to_channel(bot: Bot, user_id: int, chat_id: str) -> bool:
    """Faqat PUBLIC telegram turidagi kanallar uchun getChatMember orqali tekshiradi.

    MUHIM: TelegramRetryAfter (flood/rate-limit) alohida ushlanadi - shunda:
    - bot yiqilib qolmaydi;
    - aniq sabab logga yoziladi (qancha soniya kutish kerakligi bilan);
    - faqat SHU kanal 'tekshirib bo'lmadi' deb hisoblanadi, boshqa kanallarning
      tekshiruviga hech qanday ta'sir qilmaydi (chaqiruvchi funksiya har bir
      kanalni mustaqil ko'rib chiqadi)."""
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in MEMBER_STATUSES
    except TelegramRetryAfter as e:
        logger.warning(
            f"[check_sub] chat_id={chat_id} user_id={user_id} -> RATE LIMIT "
            f"(Telegram {e.retry_after}s kutishni so'radi)"
        )
        return False
    except TelegramBadRequest as e:
        logger.warning(f"[check_sub] chat_id={chat_id} user_id={user_id} -> TelegramBadRequest: {e}")
        return False
    except Exception as e:
        logger.warning(f"[check_sub] chat_id={chat_id} user_id={user_id} -> Exception: {e}")
        return False


async def get_unsubscribed_channels(bot: Bot, user_id: int, channels) -> list:
    """
    Har bir kanal MUSTAQIL, user_id + channel_id bo'yicha alohida tekshiriladi -
    bitta kanaldagi xatolik yoki holat boshqa kanallarga umuman ta'sir qilmaydi.

    - type == 'telegram' (PUBLIC kanal): getChatMember orqali tekshiriladi.
    - type == 'telegram_private' (Join Request kanal): Telegram API UMUMAN
      chaqirilmaydi (rate-limit xavfi yo'q) - faqat join_requests jadvalidan
      shu aniq user_id + channel_id juftligi bo'yicha yozuv borligi tekshiriladi.
    - Boshqa turlar (instagram/youtube/tiktok/website): har doim 'obuna bo'lgan'
      deb hisoblanadi, chunki ularni Telegram API orqali tekshirib bo'lmaydi.
    """
    unsubscribed = []
    for channel in channels:
        if channel["type"] == "telegram" and channel["chat_id"]:
            subscribed = await is_user_subscribed_to_channel(bot, user_id, channel["chat_id"])
            logger.info(
                f"[check_sub] PUBLIC channel_id={channel['id']} chat_id={channel['chat_id']} "
                f"user_id={user_id} -> subscribed={subscribed}"
            )
            if not subscribed:
                unsubscribed.append(channel)
        elif channel["type"] == "telegram_private":
            has_request = await db.has_active_join_request(user_id, channel["id"])
            logger.info(
                f"[check_sub] PRIVATE channel_id={channel['id']} user_id={user_id} "
                f"-> has_request={has_request}"
            )
            if not has_request:
                unsubscribed.append(channel)
    return unsubscribed

