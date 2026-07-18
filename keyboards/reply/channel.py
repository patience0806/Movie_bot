from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_ADD_CHANNEL = "➕ Link qo'shish"
BTN_CHANNEL_LIST = "📋 Linklar"
BTN_CHANNEL_EDIT = "✏️ Link tahrirlash"
BTN_CHANNEL_DELETE = "🗑 Link o'chirish"
BTN_BACK = "⬅️ Orqaga"


def get_channel_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_ADD_CHANNEL), KeyboardButton(text=BTN_CHANNEL_LIST))
    builder.row(KeyboardButton(text=BTN_CHANNEL_EDIT), KeyboardButton(text=BTN_CHANNEL_DELETE))
    builder.row(KeyboardButton(text=BTN_BACK))
    return builder.as_markup(resize_keyboard=True)