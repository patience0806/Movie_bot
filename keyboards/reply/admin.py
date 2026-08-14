from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_STATISTICS = "📊 Statistika"
BTN_CHANNELS = "📢 Kanal qo'shish"
BTN_MOVIES = "🎬 Kino qo'shish"
BTN_ADS = "📣 Reklama"
BTN_PREMIUM = "💎 Premium"
BTN_BACK = "⬅️ Orqaga"


def get_admin_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_STATISTICS))
    builder.row(KeyboardButton(text=BTN_CHANNELS), KeyboardButton(text=BTN_MOVIES))
    builder.row(KeyboardButton(text=BTN_ADS), KeyboardButton(text=BTN_PREMIUM))
    builder.row(KeyboardButton(text=BTN_BACK))
    return builder.as_markup(resize_keyboard=True)