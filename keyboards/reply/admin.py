from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_STATISTICS = "📊 Statistika"
BTN_CHANNELS = "📢 Kanal qo'shish"
BTN_MOVIES = "🎬 Kino qo'shish"
BTN_ADS = "📣 Reklama"
BTN_PREMIUM = "💎 Premium"
BTN_ADMINS = "👮 Adminlar"
BTN_BACK = "⬅️ Orqaga"


def get_admin_menu(is_owner: bool = False) -> ReplyKeyboardMarkup:
    """is_owner=True bo'lsagina '👮 Adminlar' tugmasi ko'rsatiladi - oddiy adminlar
    boshqa adminlarni boshqara olmasligi kerak."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_STATISTICS))
    builder.row(KeyboardButton(text=BTN_CHANNELS), KeyboardButton(text=BTN_MOVIES))
    builder.row(KeyboardButton(text=BTN_ADS), KeyboardButton(text=BTN_PREMIUM))
    if is_owner:
        builder.row(KeyboardButton(text=BTN_ADMINS))
    builder.row(KeyboardButton(text=BTN_BACK))
    return builder.as_markup(resize_keyboard=True)