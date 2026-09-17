from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

BTN_ADD_ADMIN = "➕ Admin qo'shish"
BTN_REMOVE_ADMIN = "🗑 Admin chiqarish"
BTN_ADMIN_LIST = "📋 Adminlar ro'yxati"
BTN_BACK = "⬅️ Orqaga"


def get_admins_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_ADD_ADMIN))
    builder.row(KeyboardButton(text=BTN_REMOVE_ADMIN))
    builder.row(KeyboardButton(text=BTN_ADMIN_LIST))
    builder.row(KeyboardButton(text=BTN_BACK))
    return builder.as_markup(resize_keyboard=True)