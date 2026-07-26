from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, ChatJoinRequest

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


@router.chat_join_request()
async def handle_chat_join_request(event: ChatJoinRequest):
    """PRIVATE (telegram_private) kanalga foydalanuvchi Join Request yuborganda
    Telegram shu update'ni yuboradi. Buning uchun bot o'sha kanalda administrator
    bo'lishi va 'Foydalanuvchilarni taklif qilish' huquqiga ega bo'lishi SHART -
    aks holda Telegram bu update'ni botga umuman yubormaydi.

    Bu yerda faqat bazaga yozib qo'yamiz (status='requested'). Foydalanuvchini
    kanalga avtomatik qabul qilish/rad etish bu yerda amalga oshirilmaydi -
    buni admin Telegram'ning o'zida qo'lda tasdiqlaydi."""
    channel = await db.get_channel_by_chat_id(str(event.chat.id))
    if channel is not None and channel["type"] == "telegram_private":
        await db.add_join_request(event.from_user.id, channel["id"])