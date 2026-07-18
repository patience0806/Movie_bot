from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message

import database as db
from config import START_TEXT
from keyboards.inline.channel import subscribe_keyboard
from keyboards.reply.user import get_user_menu

router = Router()


async def mandatory_sub_enabled() -> bool:
    value = await db.get_setting("mandatory_sub", "on")
    return value == "on"


async def get_pending_channels(bot: Bot, user_id: int):
    """Foydalanuvchi hali obuna bo'lmagan (faqat telegram turidagi) kanallarni qaytaradi."""
    from utils.check_sub import get_unsubscribed_channels

    if not await mandatory_sub_enabled():
        return []
    channels = await db.get_channels(active_only=True)
    if not channels:
        return []
    return await get_unsubscribed_channels(bot, user_id, channels)


async def send_subscription_prompt(message: Message, bot: Bot):
    channels = await db.get_channels(active_only=True)
    await message.answer(
        "📢 Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling, so'ng "
        "\"✅ Tekshirish\" tugmasini bosing:",
        reply_markup=subscribe_keyboard(channels)
    )


async def send_main_menu(message: Message, user_id: int):
    is_admin = await db.is_admin(user_id)
    text = START_TEXT.format(name=message.from_user.full_name)
    await message.answer(text, reply_markup=get_user_menu(is_admin))


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    pending = await get_pending_channels(bot, callback.from_user.id)
    if pending:
        await callback.answer("❗️ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        return
    await callback.answer("✅ Rahmat! Obuna tasdiqlandi.")
    await callback.message.delete()
    await send_main_menu(callback.message, callback.from_user.id)