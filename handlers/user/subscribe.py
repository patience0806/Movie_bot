import logging

from aiogram import Router, Bot, F
from aiogram.types import CallbackQuery, Message, ChatJoinRequest

import database as db
from config import START_TEXT
from keyboards.inline.channel import subscribe_keyboard
from keyboards.reply.user import get_user_menu

router = Router()
logger = logging.getLogger(__name__)


async def mandatory_sub_enabled() -> bool:
    value = await db.get_setting("mandatory_sub", "on")
    return value == "on"


async def get_pending_channels(bot: Bot, user_id: int):
    """Foydalanuvchi hali obuna bo'lmagan (faqat telegram turidagi) kanallarni qaytaradi.

    MUHIM: agar foydalanuvchi Premium faol bo'lsa, majburiy obuna umuman TEKSHIRILMAYDI
    va bo'sh ro'yxat qaytariladi - Premium va majburiy obuna tizimlari bir-biriga
    aralashmasligi shu yerda ta'minlanadi."""
    from utils.check_sub import get_unsubscribed_channels

    if await db.is_premium_active(user_id):
        return []

    if not await mandatory_sub_enabled():
        return []
    channels = await db.get_channels(active_only=True)
    if not channels:
        return []
    return await get_unsubscribed_channels(bot, user_id, channels)


async def send_subscription_prompt(message: Message, bot: Bot):
    """MUHIM TUZATISH: avval bu funksiya HAR DOIM barcha faol kanallarni ko'rsatar edi,
    hatto foydalanuvchi ularning ba'zilarini allaqachon bajargan bo'lsa ham (masalan
    6 tadan 5 tasini bajargan bo'lsa ham, baribir 6 tasi ko'rsatilardi). Bu chalkashlik
    va keraksiz qayta urinishlarga (va natijada Telegram'ning "Too Many Attempts"
    cheklovi kabi holatlarga) sabab bo'lardi.

    Endi FAQAT hali bajarilmagan (pending) kanallar ko'rsatiladi - foydalanuvchi
    aniq nechta va aynan qaysi kanal qolganini ko'radi."""
    pending = await get_pending_channels(bot, message.from_user.id)
    if not pending:
        pending = await db.get_channels(active_only=True)
    await message.answer(
        "📢 Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling, so'ng "
        "\"✅ Tekshirish\" tugmasini bosing:",
        reply_markup=subscribe_keyboard(pending)
    )


async def send_main_menu(message: Message, user_id: int):
    is_admin = await db.is_admin(user_id)
    text = START_TEXT.format(name=message.from_user.full_name)
    await message.answer(text, reply_markup=get_user_menu(is_admin))


@router.callback_query(F.data == "check_sub")
async def check_sub_callback(callback: CallbackQuery, bot: Bot):
    pending = await get_pending_channels(bot, callback.from_user.id)
    if pending:
        names = ", ".join(ch["name"] for ch in pending)
        logger.info(f"[check_sub] user_id={callback.from_user.id} hali obuna bo'lmagan: {names}")
        await callback.answer("❗️ Siz hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True)
        await callback.message.edit_reply_markup(reply_markup=subscribe_keyboard(pending))
        return
    await callback.answer("✅ Rahmat! Obuna tasdiqlandi.")
    await callback.message.delete()
    await send_main_menu(callback.message, callback.from_user.id)


@router.chat_join_request()
async def handle_chat_join_request(event: ChatJoinRequest):
    """PRIVATE (telegram_private) kanalga foydalanuvchi Join Request yuborganda
    Telegram shu update'ni yuboradi. Buning uchun bot o'sha kanalda administrator
    bo'lishi va 'Foydalanuvchilarni taklif qilish' huquqiga ega bo'lishi SHART.

    MUHIM: bu yerda faqat HAQIQIY Telegram update kelganda bazaga yoziladi -
    hech qachon sun'iy ravishda 'approved' qilinmaydi. Foydalanuvchini kanalga
    qabul qilish/rad etish bu yerda amalga oshirilmaydi - buni admin Telegram'ning
    o'zida qo'lda tasdiqlaydi."""
    logger.info(f"[join_request] KELDI: chat_id={event.chat.id} user_id={event.from_user.id}")
    channel = await db.get_channel_by_chat_id(str(event.chat.id))
    if channel is None:
        logger.warning(f"[join_request] chat_id={event.chat.id} uchun bazada kanal topilmadi!")
        return
    if channel["type"] != "telegram_private":
        logger.warning(
            f"[join_request] chat_id={event.chat.id} bazada '{channel['type']}' turida, "
            "'telegram_private' emas!"
        )
        return
    await db.add_join_request(event.from_user.id, channel["id"])
    logger.info(f"[join_request] SAQLANDI: channel_id={channel['id']} user_id={event.from_user.id}")

